#!/usr/bin/env python3
"""
因子筛选器 - 遍历所有因子进行回测
使用现有的 3_fastover.py 框架
"""

import argparse
import os
import sys
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from multiprocessing import Pool, cpu_count

# 添加项目根目录到路径
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg
import scripts.prepare_feather_from_csv as conv
from importlib import import_module

def get_all_factors():
    """获取所有因子名称"""
    factors_path = Path(project_root) / "factors"
    factor_set = set()
    
    # 遍历所有子目录
    for category in factors_path.iterdir():
        if category.is_dir() and not category.name.startswith('__') and category.name not in ['__pycache__', '.DS_Store']:
            for factor_file in category.glob("*.py"):
                if factor_file.name != "__init__.py":
                    factor_set.add(f"{category.name}.{factor_file.stem}")
    
    # 添加根目录下的因子
    for factor_file in factors_path.glob("*.py"):
        if factor_file.name not in ["__init__.py", "STRATEGIES_OVERVIEW.md", ".DS_Store"]:
            factor_set.add(factor_file.stem)
    
    return sorted(list(factor_set))

def ensure_pickle(symbol, interval):
    """确保pickle数据存在"""
    s = symbol if "-" in symbol else symbol.replace("USDT", "-USDT")
    pkl = os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{s}.pkl")
    if not os.path.exists(pkl):
        print(f"正在转换数据: {symbol} {interval}")
        conv.convert(symbol, interval)
    return pkl

def run_factor_backtest(params):
    """运行单个因子回测（用于多进程）"""
    factor, symbol, interval, para, start, end = params
    
    try:
        # 确保数据存在
        ensure_pickle(symbol, interval)
        
        # 读取数据
        df = pd.read_feather(os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{symbol}.pkl"))
        
        # 导入因子模块
        if "." in factor:
            mod_name = f"factors.{factor}"
        else:
            mod_name = f"factors.{factor}"
        
        # 动态导入因子
        cls = __import__(mod_name, fromlist=('',))
        
        # 计算信号
        _df = df.copy()
        
        # 检查因子期望的参数格式
        import inspect
        sig = inspect.signature(cls.signal)
        para_param = sig.parameters.get('para')
        
        # 如果因子期望列表参数，但传入的是整数，则转换为列表
        if para_param and para_param.default != inspect.Parameter.empty:
            default_para = para_param.default
            if isinstance(default_para, list) and not isinstance(para, list):
                para = [para]
        
        _df = cls.signal(_df, para=para, proportion=cfg.proportion, leverage_rate=cfg.leverage_rate)
        
        # 计算实际持仓
        from cta_api.position import position_for_future
        _df = position_for_future(_df)
        
        # 过滤时间区间
        _df = _df[(_df['candle_begin_time'] >= pd.to_datetime(start)) & (_df['candle_begin_time'] <= pd.to_datetime(end))]
        
        # 计算资金曲线
        from cta_api.function import cal_equity_curve
        min_amount = cfg.min_amount_dict.get(symbol, 0.001)
        
        # 检查是否有信号
        if _df['signal'].isna().all() or _df['signal'].sum() == 0:
            return {
                'factor': factor,
                'symbol': symbol,
                'interval': interval,
                'para': para,
                'total_return': 0,
                'annual_return': 0,
                'max_drawdown': 0,
                'sharpe': 0,
                'win_rate': 0,
                'trade_count': 0,
                'status': 'no_signal'
            }
        
        _df = cal_equity_curve(_df, slippage=cfg.slippage, c_rate=cfg.c_rate, 
                               leverage_rate=cfg.leverage_rate, min_amount=min_amount, 
                               min_margin_ratio=cfg.min_margin_ratio)
        
        # 计算指标
        equity = _df['equity_curve'].values
        if len(equity) < 2:
            return None
        
        returns = pd.Series(equity).pct_change().dropna()
        
        total_return = (equity[-1] / equity[0] - 1) * 100
        annual_return = (1 + total_return / 100) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
        max_drawdown = (pd.Series(equity).cummax() - equity).max() / pd.Series(equity).cummax().max() * 100
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
        
        # 计算胜率
        trade_count = len(_df[_df['signal'] != 0])
        win_count = len(_df[(_df['signal'] != 0) & (_df['equity_curve'] > _df['equity_curve'].shift(1))])
        win_rate = win_count / trade_count if trade_count > 0 else 0
        
        return {
            'factor': factor,
            'symbol': symbol,
            'interval': interval,
            'para': para,
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return * 100, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe': round(sharpe, 2),
            'win_rate': round(win_rate * 100, 2),
            'trade_count': trade_count,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'factor': factor,
            'symbol': symbol,
            'interval': interval,
            'para': para,
            'total_return': 0,
            'annual_return': 0,
            'max_drawdown': 0,
            'sharpe': 0,
            'win_rate': 0,
            'trade_count': 0,
            'status': f'error: {str(e)}'
        }

def main():
    parser = argparse.ArgumentParser(description="因子筛选器 - 遍历所有因子")
    parser.add_argument("--symbols", required=True, help="币种列表，如 BTC-USDT,ETH-USDT")
    parser.add_argument("--interval", default="1H", help="时间周期")
    parser.add_argument("--start", default="2021-01-01", help="开始时间")
    parser.add_argument("--end", default="2026-01-01", help="结束时间")
    parser.add_argument("--para", default="10:200:20", help="参数范围，如 '10:200:20'")
    parser.add_argument("--output", default="factor_screener_results.csv", help="输出文件")
    parser.add_argument("--limit", type=int, default=None, help="限制因子数量")
    parser.add_argument("--processes", type=int, default=1, help="多进程数量")
    parser.add_argument("--top", type=int, default=20, help="显示前N个最佳结果")
    
    args = parser.parse_args()
    
    # 获取所有因子
    all_factors = get_all_factors()
    if args.limit:
        all_factors = all_factors[:args.limit]
    
    print(f"🔍 找到 {len(all_factors)} 个因子")
    print(f"前5个因子: {all_factors[:5]}")
    
    # 解析参数
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    
    # 解析参数范围
    if "," in args.para:
        para_list = [int(x.strip()) for x in args.para.split(",") if x.strip()]
    elif ":" in args.para:
        a, b, c = [int(x) for x in args.para.split(":")]
        para_list = list(range(a, b + 1, c))
    else:
        para_list = [int(args.para)]
    
    # 生成任务列表
    tasks = []
    for factor in all_factors:
        for symbol in syms:
            for para in para_list:
                tasks.append((factor, symbol, args.interval, para, args.start, args.end))
    
    print(f"\n📊 回测配置:")
    print(f"  币种: {', '.join(syms)}")
    print(f"  周期: {args.interval}")
    print(f"  时间: {args.start} ~ {args.end}")
    print(f"  参数: {para_list} ({len(para_list)}个)")
    print(f"  总任务数: {len(tasks)}")
    print(f"  多进程: {args.processes}")
    
    # 运行回测
    print(f"\n🚀 开始回测...")
    start_time = time.time()
    
    results = []
    if args.processes > 1 and len(tasks) > 10:
        # 多进程
        with Pool(processes=min(args.processes, cpu_count())) as pool:
            for i, result in enumerate(pool.imap_unordered(run_factor_backtest, tasks), 1):
                if result:
                    results.append(result)
                if i % 10 == 0 or i == len(tasks):
                    progress = i / len(tasks) * 100
                    elapsed = time.time() - start_time
                    print(f"  进度: {i}/{len(tasks)} ({progress:.1f}%) - 耗时: {elapsed:.1f}s")
    else:
        # 单进程
        for i, task in enumerate(tasks, 1):
            result = run_factor_backtest(task)
            if result:
                results.append(result)
            if i % 10 == 0 or i == len(tasks):
                progress = i / len(tasks) * 100
                elapsed = time.time() - start_time
                print(f"  进度: {i}/{len(tasks)} ({progress:.1f}%) - 耗时: {elapsed:.1f}s")
    
    # 保存结果
    if results:
        df_results = pd.DataFrame(results)
        output_path = os.path.join(str(project_root), "data", "output", args.output)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_results.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # 统计
        success_results = df_results[df_results['status'] == 'success']
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"✅ 回测完成!")
        print(f"{'='*80}")
        print(f"总耗时: {elapsed_time:.1f} 秒")
        print(f"成功: {len(success_results)}/{len(results)} ({len(success_results)/len(results)*100:.1f}%)")
        print(f"结果保存: {output_path}")
        
        if not success_results.empty:
            # 按不同指标排序显示
            print(f"\n📈 最佳结果 (按年化收益):")
            best_by_annual = success_results.nlargest(min(args.top, len(success_results)), 'annual_return')
            for _, row in best_by_annual.iterrows():
                para_str = str(row['para'])
                print(f"  {row['factor']:<30} {row['symbol']:<10} 参数={para_str:<10} 年化={row['annual_return']:>6}% 总收益={row['total_return']:>6}% DD={row['max_drawdown']:>6}% Sharpe={row['sharpe']:>6.2f} 胜率={row['win_rate']:>5}% 交易={row['trade_count']}")
            
            print(f"\n🎯 最佳夏普比率:")
            best_by_sharpe = success_results.nlargest(min(5, len(success_results)), 'sharpe')
            for _, row in best_by_sharpe.iterrows():
                para_str = str(row['para'])
                print(f"  {row['factor']:<30} {row['symbol']:<10} 参数={para_str:<10} Sharpe={row['sharpe']:>6.2f} 年化={row['annual_return']:>6}% DD={row['max_drawdown']:>6}%")
            
            print(f"\n🛡️ 最低回撤:")
            best_by_dd = success_results.nsmallest(5, 'max_drawdown')
            for _, row in best_by_dd.iterrows():
                para_str = str(row['para'])
                print(f"  {row['factor']:<30} {row['symbol']:<10} 参数={para_str:<10} DD={row['max_drawdown']:>6}% 年化={row['annual_return']:>6}% Sharpe={row['sharpe']:>6.2f}")
        
        # 保存汇总统计
        summary_file = os.path.join(str(project_root), "data", "output", f"summary_{args.output}")
        summary = success_results.groupby(['factor', 'symbol']).agg({
            'annual_return': ['mean', 'max'],
            'max_drawdown': ['min', 'mean'],
            'sharpe': ['max', 'mean'],
            'para': 'count'
        }).round(2)
        summary.to_csv(summary_file, encoding='utf-8-sig')
        print(f"\n📊 汇总统计保存: {summary_file}")
        
    else:
        print("\n❌ 没有成功的结果")

if __name__ == "__main__":
    main()