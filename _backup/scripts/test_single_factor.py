#!/usr/bin/env python3
"""
测试单个因子的回测
"""

import os
import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg
import scripts.prepare_feather_from_csv as conv

def test_factor(factor_name, symbol, interval, para, start, end):
    """测试单个因子"""
    try:
        print(f"测试因子: {factor_name}")
        
        # 确保数据存在
        s = symbol if "-" in symbol else symbol.replace("USDT", "-USDT")
        pkl = os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{s}.pkl")
        if not os.path.exists(pkl):
            print(f"正在转换数据: {symbol} {interval}")
            conv.convert(symbol, interval)
        
        # 读取数据
        df = pd.read_feather(pkl)
        print(f"数据形状: {df.shape}")
        
        # 导入因子模块
        if "." in factor_name:
            mod_name = f"factors.{factor_name}"
        else:
            mod_name = f"factors.{factor_name}"
        
        print(f"导入模块: {mod_name}")
        cls = __import__(mod_name, fromlist=('',))
        
        # 检查 signal 函数是否存在
        if not hasattr(cls, 'signal'):
            print(f"错误: {factor_name} 没有 signal 函数")
            return False
        
        # 计算信号
        _df = df.copy()
        print(f"调用 signal 函数，参数: para={para}, proportion={cfg.proportion}, leverage_rate={cfg.leverage_rate}")
        _df = cls.signal(_df, para=para, proportion=cfg.proportion, leverage_rate=cfg.leverage_rate)
        
        print(f"计算后数据形状: {_df.shape}")
        print(f"信号列: {_df.columns.tolist()}")
        
        if 'signal' not in _df.columns:
            print("错误: 没有 signal 列")
            return False
        
        # 计算实际持仓
        from cta_api.position import position_for_future
        _df = position_for_future(_df)
        
        # 过滤时间区间
        _df = _df[(_df['candle_begin_time'] >= pd.to_datetime(start)) & (_df['candle_begin_time'] <= pd.to_datetime(end))]
        
        # 计算资金曲线
        from cta_api.function import cal_equity_curve
        min_amount = cfg.min_amount_dict.get(symbol, 0.001)
        _df = cal_equity_curve(_df, slippage=cfg.slippage, c_rate=cfg.c_rate, 
                               leverage_rate=cfg.leverage_rate, min_amount=min_amount, 
                               min_margin_ratio=cfg.min_margin_ratio)
        
        # 计算指标
        equity = _df['equity_curve'].values
        if len(equity) < 2:
            print("错误: 资金曲线数据不足")
            return False
        
        returns = pd.Series(equity).pct_change().dropna()
        
        total_return = (equity[-1] / equity[0] - 1) * 100
        annual_return = (1 + total_return / 100) ** (252 / len(returns)) - 1 if len(returns) > 0 else 0
        max_drawdown = (pd.Series(equity).cummax() - equity).max() / pd.Series(equity).cummax().max() * 100
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0
        
        print(f"\n✅ 回测成功!")
        print(f"  总收益: {total_return:.2f}%")
        print(f"  年化收益: {annual_return*100:.2f}%")
        print(f"  最大回撤: {max_drawdown:.2f}%")
        print(f"  夏普比率: {sharpe:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 测试 sma 因子
    test_factor("sma", "BTC-USDT", "1H", 100, "2024-01-01", "2024-12-31")