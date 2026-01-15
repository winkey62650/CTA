import pandas as pd
import importlib
import os
import sys
from joblib import Parallel, delayed
from typing import List, Optional
from pathlib import Path
import warnings

from cta_api.base import BacktestConfig
from cta_api.engine import BacktestEngine
import config as global_config

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def find_all_factors(root_path: Path) -> List[str]:
    """
    Find all factor modules in the factors directory.
    Returns a list of factor names like 'trend.ema_cross'.
    """
    factors_dir = root_path / 'factors'
    factor_names = []
    
    for root, dirs, files in os.walk(factors_dir):
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                # Construct relative path from factors dir
                rel_path = Path(root).relative_to(factors_dir)
                if str(rel_path) == '.':
                    # Directly under factors/
                    module_name = file[:-3]
                else:
                    # Under subdirectory
                    module_name = f"{str(rel_path).replace(os.sep, '.')}.{file[:-3]}"
                
                factor_names.append(module_name)
    
    return sorted(factor_names)

def run_single_param_set(engine: BacktestConfig, symbol: str, factor_name: str, para: list, rule_type: str, start: str, end: str):
    """
    Run a single backtest task.
    """
    try:
        df, metrics = engine.run_backtest(
            symbol=symbol,
            factor_name=factor_name,
            para=para,
            rule_type=rule_type,
            start_date=start,
            end_date=end,
            show_chart=False
        )
        
        if df is None or df.empty:
            return None
        
        # Basic result info
        res = {
            'symbol': symbol,
            'factor': factor_name,
            'para': str(para)
        }
        
        # Add metrics if available
        if metrics is not None:
            # Add all calculated metrics to the result dictionary
            for metric in metrics.index:
                res[metric] = metrics.loc[metric, 0]
        else:
            # Fallback if metrics calculation failed
            res['年化收益'] = 0
            
        return res
        
    except Exception as e:
        print(f"Error in {factor_name} {para}: {e}")
        return None

def main():
    symbol = getattr(global_config, "full_symbol", "BTC-USDT")
    if getattr(global_config, "rule_type_list", None):
        default_rule = global_config.rule_type_list[0]
    else:
        default_rule = "1h"
    rule_type = getattr(global_config, "full_rule_type", default_rule)
    start = getattr(global_config, "full_start", getattr(global_config, "date_start", "2021-01-01"))
    end = getattr(global_config, "full_end", getattr(global_config, "date_end", "2025-01-01"))
    cpu = getattr(global_config, "full_cpu", max(1, os.cpu_count() - 1))
    limit = getattr(global_config, "full_limit", 0)
    category = getattr(global_config, "full_category", None)
    
    print(f"Starting Full Batch Backtest for {symbol}...")
    print(f"Time Range: {start} to {end}")
    
    # 1. Initialize Engine
    cfg = BacktestConfig(
        c_rate=global_config.c_rate,
        slippage=global_config.slippage,
        leverage_rate=global_config.leverage_rate,
        min_margin_ratio=global_config.min_margin_ratio,
        proportion=global_config.proportion
    )
    engine = BacktestEngine(cfg)
    
    # 2. Find Factors
    all_factors = find_all_factors(engine.root_path)
    
    if category:
        all_factors = [f for f in all_factors if f.startswith(category)]
        
    print(f"Found {len(all_factors)} factors.")
    
    # 3. Generate Tasks
    tasks = []
    for factor_name in all_factors:
        try:
            module = importlib.import_module(f'factors.{factor_name}')
            
            # Get parameter list
            para_list = []
            if hasattr(module, 'Strategy'):
                # Class based
                if hasattr(module.Strategy, 'para_list'):
                    # Check if para_list is static or instance method
                    # Usually instance method in this codebase, but let's try both
                    try:
                        para_list = module.Strategy.para_list()
                    except:
                        para_list = module.Strategy().para_list()
            elif hasattr(module, 'para_list'):
                # Function based
                para_list = module.para_list()
            
            if not para_list:
                # print(f"Skipping {factor_name}: No para_list found or empty.")
                continue
                
            # Add tasks
            for para in para_list:
                # Filter out factors with 3 parameters as requested
                if len(para) == 3:
                    continue
                    
                tasks.append((engine, symbol, factor_name, para, rule_type, start, end))
                
                # Check limit
                if limit > 0 and len(tasks) >= limit:
                    break
            
            if limit > 0 and len(tasks) >= limit:
                break
                
        except Exception as e:
            print(f"Error loading factor {factor_name}: {e}")
            continue
            
    print(f"Total tasks generated: {len(tasks)}")
    
    if not tasks:
        print("No tasks to run.")
        return

    # 4. Run Tasks in Parallel
    print(f"Running backtests on {cpu} cores...")
    results = Parallel(n_jobs=cpu)(delayed(run_single_param_set)(*task) for task in tasks)
    
    # 5. Process Results
    results = [r for r in results if r is not None]
    
    if results:
        df_res = pd.DataFrame(results)
        
        # Sort by Annual Return
        if '年化收益' in df_res.columns:
            df_res = df_res.sort_values(by='年化收益', ascending=False)
        
        # Output paths
        csv_path = engine.output_path / f'full_backtest_{symbol}_{rule_type}.csv'
        xlsx_path = engine.output_path / f'full_backtest_{symbol}_{rule_type}.xlsx'
        
        # Save
        df_res.to_csv(csv_path, index=False, encoding='utf-8-sig')
        try:
            df_res.to_excel(xlsx_path, index=False)
            print(f"\nResults saved to:\n- {csv_path}\n- {xlsx_path}")
        except ImportError:
            print(f"\nResults saved to {csv_path} (install openpyxl for Excel support)")
        
        # Print Top 10
        print("\nTop 10 Factors by Annual Return:")
        print(df_res[['factor', 'para', '年化收益', '夏普比率', '最大回撤']].head(10).to_string())
        
    else:
        print("No valid results returned.")

if __name__ == "__main__":
    main()
