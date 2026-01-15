#!/usr/bin/env python3
"""
遍历所有因子进行批量回测的脚本
支持指定币种、时间区间、参数范围
"""

import argparse
import os
import sys
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg
import scripts.prepare_feather_from_csv as conv
from importlib import import_module

def get_all_factors():
    """获取所有因子名称"""
    factors_path = project_root / "factors"
    factor_list = []
    
    # 遍历所有子目录
    for category in factors_path.iterdir():
        if category.is_dir() and not category.name.startswith('__'):
            for factor_file in category.glob("*.py"):
                if factor_file.name != "__init__.py":
                    factor_list.append(f"{category.name}.{factor_file.stem}")
        elif category.is_file() and category.suffix == '.py' and category.name not in ['__init__.py', 'STRATEGIES_OVERVIEW.md']:
            factor_list.append(category.stem)
    
    # 添加根目录下的因子
    for factor_file in factors_path.glob("*.py"):
        if factor_file.name not in ["__init__.py", "STRATEGIES_OVERVIEW.md"]:
            factor_list.append(factor_file.stem)
    
    return sorted(factor_list)

def ensure_pickle(symbol, interval):
    """确保pickle数据存在"""
    s = symbol if "-" in symbol else symbol.replace("USDT", "-USDT")
    pkl = os.path.join(project_root, "data", "pickle_data", interval.upper(), f"{s}.pkl")
    if not os.path.exists(pkl):
        print(f"正在转换数据: {symbol} {interval}")
        conv.convert(symbol, interval)
    return pkl

def gen_para_list(pstr):
    """生成参数列表"""
    if "," in pstr:
        parts = [x.strip() for x in pstr.split(",") if x.strip()]
        return [int(x) for x in parts]
    if ":" in pstr:
        a, b, c = [int(x) for x in pstr.split(":")]
        return list(range(a, b + 1, c))
    return [int(pstr)]

def run_single_backtest(factor, symbol, interval, start, end, para, min_amount):
    """运行单个因子的回测"""
    try:
        # 确保数据存在
        ensure_pickle(symbol, interval)
        
        # 读取数据
        df = pd.read_feather(os.path.join(project_root, "data", "pickle_data", interval.upper(), f"{symbol}.pkl"))
        
        # 导入因子模块
        if "." in factor:
            # 带目录的因子
            mod_name = f"factors.{factor}"
        else:
            # 根目录因子
            mod_name = f"factors.{factor}"
        
        mod = import_module(mod_name)
        
        # 计算信号
        cfg.signal_name_list = [factor]
        cfg.rule_type_list = [interval]
        cfg.date_start = start
        cfg.date_end = end
        cfg.para = [para]
        
        # 调用回测核心
        from cta_api.cta_core import base_data, stg_date
        
        # 设置配置
        cfg.symbol_list = [symbol]
        
        # 运行回测
        base_data(cfg.symbol_list, interval, multiple_process=False)
        stg_date(cfg.symbol_list, interval, multiple_process=False)
        
        # 读取结果
        result_file = os.path.join(project_root, "data", "output", "equity_curve", f"{factor}&{symbol}&{interval}&[{para}].csv")
        if os.path.exists(result_file):
            result_df = pd.read_csv(result_file)
            if not result_df.empty:
                # 计算基础指标
                equity = result_df['equity_curve'].values
                returns = pd.Series(equity).pct_change().dropna()
                
                total_return = (equity[-1] / equity[0] - 1) * 100
                annual_return = (1 + total_return / 100) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
                max_drawdown = (pd.Series(equity).cummax() - equity).max() / pd.Series(equity).cummax().max() * 100
                sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
                
                return {
                    'factor': factor,
                    'symbol': symbol,
                    'interval': interval,
                    'para': para,
                    'total_return': round(total_return, 2),
                    'annual_return': round(annual_return * 100, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'sharpe': round(sharpe, 2),
                    'status': 'success'
                }
        
        return {
            'factor': factor,
            'symbol': symbol,
            'interval': interval,
            'para': para,
            'total_return': 0,
            'annual_return': 0,
            'max_drawdown': 0,
            'sharpe': 0,
            'status': 'no_data'
        }
        
    except Exception as e:
        print(f"回测失败 {factor}@{symbol}: {e}")
        return {
            'factor': factor,
            'symbol': symbol,
            'interval': interval,
            'para': para,
            'total_return': 0,
            'annual_return': 0,
            'max_drawdown': 0,
            'sharpe': 0,
            'status': f'error: {str(e)}'
        }

def main():
    parser = argparse.ArgumentParser(description="遍历所有因子进行批量回测")
    parser.add_argument("--symbols", required=True, help="币种列表，逗号分隔，如 BTC-USDT,ETH-USDT")
    parser.add_argument("--interval", default="1H", help="时间周期，如 1H, 4H, 1D")
    parser.add_argument("--start", default="2021-01-01", help="开始时间")
    parser.add_argument("--end", default="2026-01-01", help="结束时间")
    parser.add_argument("--para", default="10:200:10", help="参数范围，如 '10:200:10' 或 '5,10,15'")
    parser.add_argument("--output", default="all_factors_results.csv", help="输出文件名")
    parser.add_argument("--limit", type=int, default=None, help="限制测试的因子数量（用于测试）")
    
    args = parser.parse_args()
    
    # 获取所有因子
    all_factors = get_all_factors()
    
    if args.limit:
        all_factors = all_factors[:args.limit]
    
    print(f"找到 {len(all_factors)} 个因子:")
    for i, f in enumerate(all_factors, 1):
        print(f"  {i:2d}. {f}")
    
    # 解析参数
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    para_list = gen_para_list(args.para)
    
    print(f"\n开始回测配置:")
    print(f"  币种: {syms}")
    print(f"  周期: {args.interval}")
    print(f"  时间: {args.start} ~ {args.end}")
    print(f"  参数: {para_list}")
    print(f"  预计回测次数: {len(all_factors) * len(syms) * len(para_list)}")
    
    # 收集结果
    results = []
    total_tests = len(all_factors) * len(syms) * len(para_list)
    completed_tests = 0
    
    start_time = time.time()
    
    for factor in all_factors:
        print(f"\n{'='*60}")
        print(f"测试因子: {factor}")
        print(f"{'='*60}")
        
        for symbol in syms:
            print(f"\n币种: {symbol}")
            
            for para in para_list:
                completed_tests += 1
                print(f"  [{completed_tests}/{total_tests}] 参数 {para} ...", end="", flush=True)
                
                result = run_single_backtest(factor, symbol, args.interval, args.start, args.end, para, cfg.min_amount_dict.get(symbol, 0.001))
                results.append(result)
                
                if result['status'] == 'success':
                    print(f" ✓ 收益:{result['total_return']}% 年化:{result['annual_return']}% DD:{result['max_drawdown']}% Sharpe:{result['sharpe']}")
                else:
                    print(f" ✗ {result['status']}")
                
                # 保存中间结果
                if len(results) % 10 == 0:
                    df_results = pd.DataFrame(results)
                    temp_path = os.path.join(project_root, "data", "output", f"temp_{args.output}")
                    df_results.to_csv(temp_path, index=False, encoding='utf-8-sig')
                    print(f"  已保存临时结果: {len(results)} 条")
    
    # 保存最终结果
    df_results = pd.DataFrame(results)
    output_path = os.path.join(project_root, "data", "output", args.output)
    df_results.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 计算统计
    elapsed_time = time.time() - start_time
    success_count = len(df_results[df_results['status'] == 'success'])
    
    print(f"\n{'='*60}")
    print(f"回测完成!")
    print(f"{'='*60}")
    print(f"总耗时: {elapsed_time:.1f} 秒")
    print(f"成功: {success_count}/{len(results)}")
    print(f"结果保存: {output_path}")
    
    # 显示最佳结果
    if success_count > 0:
        print(f"\n最佳结果 (按年化收益):")
        best = df_results[df_results['status'] == 'success'].nlargest(5, 'annual_return')
        for _, row in best.iterrows():
            print(f"  {row['factor']}@{row['symbol']} 参数={row['para']}: 年化={row['annual_return']}% 总收益={row['total_return']}% DD={row['max_drawdown']}% Sharpe={row['sharpe']}")

if __name__ == "__main__":
    main()