import pandas as pd
import importlib
import os
from joblib import Parallel, delayed
from typing import List
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import ast

from cta_api.base import BacktestConfig, BaseFactor
from cta_api.engine import BacktestEngine
import config as global_config

matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "STHeiti", "PingFang SC", "Arial Unicode MS"]
matplotlib.rcParams["axes.unicode_minus"] = False


def _parse_para_str(s):
    try:
        v = ast.literal_eval(s)
    except Exception:
        return [s]
    if isinstance(v, (list, tuple)):
        return list(v)
    return [v]


def plot_param_surface(res_df: pd.DataFrame, metric: str = '夏普比率'):
    if 'para' not in res_df.columns or metric not in res_df.columns:
        return
    para_list = res_df['para'].apply(_parse_para_str)
    max_len = para_list.map(len).max()
    if max_len == 1:
        res_df['_p1'] = para_list.apply(lambda x: x[0])
        df_sorted = res_df.sort_values('_p1')
        fig, ax = plt.subplots()
        ax.plot(df_sorted['_p1'], df_sorted[metric])
        ax.set_xlabel('param1')
        ax.set_ylabel(metric)
        ax.set_title('Parameter surface (1D)')
        plt.tight_layout()
        plt.show()
    elif max_len == 2:
        res_df['_p1'] = para_list.apply(lambda x: x[0])
        res_df['_p2'] = para_list.apply(lambda x: x[1])
        pivot = res_df.pivot_table(index='_p1', columns='_p2', values=metric)
        if pivot.isna().all().all():
            return
        fig, ax = plt.subplots()
        cax = ax.imshow(pivot.values, origin='lower', aspect='auto')
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xlabel('param2')
        ax.set_ylabel('param1')
        ax.set_title(f'{metric} surface (2D)')
        fig.colorbar(cax, ax=ax)
        plt.tight_layout()
        plt.show()


def plot_param_surfaces_multi(res_df: pd.DataFrame):
    if 'para' not in res_df.columns:
        return
    metrics = ['年化收益', '年化收益/回撤比', '夏普比率']
    available = [m for m in metrics if m in res_df.columns]
    if not available:
        return
    para_list = res_df['para'].apply(_parse_para_str)
    max_len = para_list.map(len).max()
    if max_len == 1:
        res_df['_p1'] = para_list.apply(lambda x: x[0])
        df_sorted = res_df.sort_values('_p1')
        fig, axes = plt.subplots(len(available), 1, sharex=True)
        if len(available) == 1:
            axes = [axes]
        for ax, m in zip(axes, available):
            y = pd.to_numeric(df_sorted[m], errors='coerce')
            ax.plot(df_sorted['_p1'], y)
            ax.set_ylabel(m)
        axes[-1].set_xlabel('参数')
        plt.tight_layout()
        plt.show()
    elif max_len == 2:
        res_df['_p1'] = para_list.apply(lambda x: x[0])
        res_df['_p2'] = para_list.apply(lambda x: x[1])
        fig, axes = plt.subplots(len(available), 1, sharex=False)
        if len(available) == 1:
            axes = [axes]
        for ax, m in zip(axes, available):
            pivot = res_df.pivot_table(index='_p1', columns='_p2', values=m)
            if pivot.isna().all().all():
                continue
            cax = ax.imshow(pivot.values, origin='lower', aspect='auto')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            ax.set_xlabel('参数2')
            ax.set_ylabel('参数1')
            ax.set_title(m)
            fig.colorbar(cax, ax=ax)
        plt.tight_layout()
        plt.show()

def run_single_param_set(engine: BacktestEngine, symbol: str, factor_name: str, para: list, rule_type: str, start: str, end: str):
    """
    单个参数组合的运行函数（用于并行调用）
    """
    try:
        # 运行回测，不画图以节省资源
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
        
        # 提取最后一行结果
        res = df.iloc[-1].to_dict()
        res['symbol'] = symbol
        res['factor'] = factor_name
        res['para'] = str(para)
        
        # 补充一些统计指标 (从 metrics 中提取)
        if metrics is not None:
            res['年化收益'] = metrics.loc['年化收益', 0]
            res['最大回撤'] = metrics.loc['最大回撤', 0]
            res['夏普比率'] = metrics.loc['夏普比率', 0]
            res['年化收益/回撤比'] = metrics.loc['年化收益/回撤比', 0]
        
        return res
    except Exception as e:
        print(f"Error in {symbol} {para}: {e}")
        return None

def main():
    symbols = getattr(global_config, "symbol_list", None)
    if not symbols:
        print("config.symbol_list is empty.")
        return

    if getattr(global_config, "signal_name_list", None):
        factor = global_config.signal_name_list[0]
        print(f"Using factor from config.signal_name_list: {factor}")
    else:
        print("config.signal_name_list is empty.")
        return

    if getattr(global_config, "rule_type_list", None):
        rule_type = global_config.rule_type_list[0]
    else:
        rule_type = "1H"

    start = getattr(global_config, "date_start", "2021-01-01")
    end = getattr(global_config, "date_end", "2025-01-01")
    cpu = getattr(global_config, "batch_cpu", max(1, os.cpu_count() - 1))
    
    # 1. 初始化配置
    cfg = BacktestConfig(
        c_rate=global_config.c_rate,
        slippage=global_config.slippage,
        leverage_rate=global_config.leverage_rate,
        min_margin_ratio=global_config.min_margin_ratio,
        proportion=global_config.proportion
    )
    engine = BacktestEngine(cfg)

    use_factor_params = getattr(global_config, "batch_use_factor_params", False)

    para_combinations = []
    
    if use_factor_params:
        # 从因子文件中加载推荐参数
        try:
            module = importlib.import_module(f'factors.{factor}')
            if hasattr(module, 'Strategy'):
                 # Class based
                 para_combinations = module.Strategy().para_list()
            elif hasattr(module, 'para_list'):
                 # Function based
                 para_combinations = module.para_list()
            else:
                print(f"No para_list found in {factor}")
                return
        except Exception as e:
            print(f"Error loading factor {factor}: {e}")
            return
    else:
        cfg_para = getattr(global_config, 'para', None)
        if cfg_para is None:
            print("Please specify parameters via --use-factor-params, --para or config.para")
            return
        if isinstance(cfg_para, (int, float)):
            para_combinations = [[cfg_para]]
        elif isinstance(cfg_para, list):
            if len(cfg_para) == 0:
                print("config.para is empty.")
                return
            first = cfg_para[0]
            if isinstance(first, (int, float)):
                para_combinations = [[x] for x in cfg_para]
            elif isinstance(first, (list, tuple)):
                para_combinations = [list(x) for x in cfg_para]
            else:
                print("config.para list element type not supported.")
                return
        else:
            print("config.para format not supported, expected int/float or list.")
            return

    total_tasks = len(symbols) * len(para_combinations)
    print(f"Total combinations: {total_tasks}")
    
    # 3. 并行执行（带简单进度打印）
    tasks = []
    for symbol in symbols:
        for para in para_combinations:
            tasks.append((engine, symbol, factor, para, rule_type, start, end))
    
    completed = 0

    def _run_with_progress(args):
        nonlocal completed
        res = run_single_param_set(*args)
        completed += 1
        print(f"\rProgress: {completed}/{total_tasks} ({completed/total_tasks*100:.1f}%)", end="", flush=True)
        return res

    results = Parallel(n_jobs=cpu)(
        delayed(_run_with_progress)(task) for task in tasks
    )
    print()  # 换行，避免进度条和后续输出混在一行
    
    # 4. 汇总结果
    results = [r for r in results if r is not None]
    if results:
        res_df = pd.DataFrame(results)
        
        # Sort by Sharpe Ratio (if available) or Return
        sort_col = '夏普比率' if '夏普比率' in res_df.columns else '年化收益'
        res_df = res_df.sort_values(by=sort_col, ascending=False)
        
        print(f"\nTop 10 Results (sorted by {sort_col}):")
        print(res_df.head(10))

        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

        # 按因子-币种输出结果文件，并设置图标题为 因子-币种
        for sym in sorted(res_df["symbol"].unique()):
            sub = res_df[res_df["symbol"] == sym]
            if sub.empty:
                continue
            folder_name = f"{factor}--{sym}"
            sym_output_dir = engine.output_path / folder_name
            sym_output_dir.mkdir(parents=True, exist_ok=True)

            excel_path = sym_output_dir / f"batch_results_{folder_name}_{timestamp}.xlsx"
            try:
                sub.to_excel(excel_path, index=False)
                print(f"Results saved to {excel_path}")
            except Exception as e:
                print(f"Error saving to Excel for {sym}: {e}")
                csv_path = sym_output_dir / f"batch_results_{folder_name}_{timestamp}.csv"
                sub.to_csv(csv_path, index=False)
                print(f"Results saved to {csv_path}")

            print(f"\nPlotting parameter surfaces for {folder_name} ...")
            try:
                plot_param_surfaces_multi(sub)
                plt.suptitle(folder_name)
            except Exception as e:
                print(f"Param surface plot failed for {sym}: {e}")
    else:
        print("No results generated.")

if __name__ == "__main__":
    main()
