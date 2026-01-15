import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib
import matplotlib.pyplot as plt
import os
import sys
import importlib

# Add root to path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

from cta_api.engine import BacktestEngine
from cta_api.base import BacktestConfig
import config as global_config

matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "STHeiti", "PingFang SC", "Arial Unicode MS"]
matplotlib.rcParams["axes.unicode_minus"] = False

def run_multi_factor_analysis(factor_path='momentum.macd', symbol='BTC-USDT'):
    factor_path = getattr(global_config, "multi_factor_path", factor_path)
    symbol = getattr(global_config, "multi_factor_symbol", symbol)
    print(f"Starting Multi-factor Analysis for {factor_path}...")
    
    # 1. Define Parameter Grid (Fast, Slow, Signal)
    # MACD standard: 12, 26, 9
    fast_range = range(8, 20, 4) # 8, 12, 16
    slow_range = range(20, 40, 5) # 20, 25, 30, 35
    signal_range = range(5, 15, 3) # 5, 8, 11, 14
    
    import itertools
    combinations = list(itertools.product(fast_range, slow_range, signal_range))
    # Filter invalid: Fast < Slow
    combinations = [c for c in combinations if c[0] < c[1]]
    
    print(f"Total combinations: {len(combinations)}")
    
    
    start_date = getattr(global_config, "multi_factor_start", "2023-01-01")
    end_date = getattr(global_config, "multi_factor_end", "2024-01-01")
    
    for i, para in enumerate(combinations):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(combinations)}")
            
        try:
            df, metrics = engine.run_backtest(
                symbol=symbol,
                factor_name=factor_path,
                para=list(para),
                rule_type='1H',
                start_date=start_date,
                end_date=end_date,
                show_chart=False
            )
            
            if metrics is not None:
                res = {
                    'fast': para[0],
                    'slow': para[1],
                    'signal': para[2],
                    'sharpe': metrics.loc['夏普比率', 0],
                    'return': metrics.loc['年化收益', 0]
                }
                results.append(res)
        except Exception as e:
            print(f"Error: {e}")
            
    df_res = pd.DataFrame(results)
    if df_res.empty:
        print("No results.")
        return

    print("Backtest complete. Analyzing...")
    
    # 3. PCA Analysis
    # Focus on High Sharpe Sets
    threshold = df_res['sharpe'].quantile(0.7) # Top 30%
    high_perf_df = df_res[df_res['sharpe'] >= threshold].copy()
    
    print(f"Top 30% threshold: Sharpe >= {threshold:.4f}")
    print(f"High performance count: {len(high_perf_df)}")
    
    if len(high_perf_df) > 3:
        X = high_perf_df[['fast', 'slow', 'signal']].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(X_scaled)
        
        print("\nPCA Explained Variance Ratio:")
        print(pca.explained_variance_ratio_)
        
        print("\nPCA Components (Eigenvectors):")
        print(pd.DataFrame(pca.components_, columns=['fast', 'slow', 'signal'], index=['PC1', 'PC2']))
        
        # 4. Sensitivity Analysis
        # Simple correlation
        corr = df_res.corr()['sharpe'].drop(['sharpe', 'return'])
        print("\nParameter Sensitivity (Correlation with Sharpe):")
        print(corr)
        
        # Generate Report
        with open('Multi_Factor_Analysis_Report.md', 'w', encoding='utf-8') as f:
            f.write(f"# Multi-Factor Analysis Report: {factor_path}\n\n")
            f.write(f"## 1. Overview\n")
            f.write(f"- Symbol: {symbol}\n")
            f.write(f"- Date Range: {start_date} to {end_date}\n")
            f.write(f"- Parameter Space Size: {len(combinations)}\n\n")
            
            f.write(f"## 2. Top Performance Statistics\n")
            f.write(f"- Max Sharpe: {df_res['sharpe'].max():.4f}\n")
            f.write(f"- Top 30% Threshold: {threshold:.4f}\n\n")
            
            f.write(f"## 3. Parameter Sensitivity\n")
            f.write("Correlation of parameters with Sharpe Ratio:\n")
            f.write("```\n")
            f.write(corr.to_string())
            f.write("\n```\n\n")
            
            f.write(f"## 4. PCA Analysis (Dimensionality Reduction)\n")
            f.write(f"Explained Variance Ratio: {pca.explained_variance_ratio_}\n\n")
            f.write("Principal Components:\n")
            f.write("```\n")
            f.write(pd.DataFrame(pca.components_, columns=['fast', 'slow', 'signal'], index=['PC1', 'PC2']).to_string())
            f.write("\n```\n\n")
            f.write("Interpretation: High weights indicate direction of maximum variance in the successful parameter set.\n")
            
        print("Multi_Factor_Analysis_Report.md generated.")
        
if __name__ == "__main__":
    run_multi_factor_analysis()
