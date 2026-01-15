"""
Choppiness Index (波动指数)

原理:
Choppiness Index 用于衡量市场是处于趋势中还是震荡中。
值越低 (通常 < 38.2) 表示趋势越强。
值越高 (通常 > 61.8) 表示震荡越剧烈。
本策略在 Choppiness Index 跌破 50 (趋势增强) 时，顺应当前价格相对于EMA的方向开仓。

参数:
- n: 周期 (推荐 14)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 1. 计算 True Range
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    
    # 2. Sum of TR
    sum_tr = df['tr'].rolling(window=n).sum()
    
    # 3. Range of High-Low
    max_high = df['high'].rolling(window=n).max()
    min_low = df['low'].rolling(window=n).min()
    range_hl = max_high - min_low
    
    # 4. Choppiness Index
    # CI = 100 * log10(SumTR / RangeHL) / log10(n)
    # 避免除以0
    range_hl = range_hl.replace(0, 0.00001)
    
    df['ci'] = 100 * np.log10(sum_tr / range_hl) / np.log10(n)
    
    # 辅助判断趋势方向: EMA(n)
    df['ema'] = df['close'].ewm(span=n, adjust=False).mean()
    
    # 策略逻辑
    # 当 CI < 50 时，认为进入趋势状态
    # 如果 Price > EMA，做多
    # 如果 Price < EMA，做空
    
    trend_mode = df['ci'] < 50
    bullish = df['close'] > df['ema']
    bearish = df['close'] < df['ema']
    
    # 开多: 进入趋势模式 且 价格在均线上
    # 或者 已经在趋势模式中 且 价格金叉均线
    # 简单起见：每当 CI < 50 且 Bullish 时保持多头
    
    # 信号生成：状态翻转
    # 状态: 1 (Long), -1 (Short), 0 (Cash)
    
    # 这是一个状态机逻辑，转化为信号点
    
    target_pos = pd.Series(0, index=df.index)
    target_pos.loc[trend_mode & bullish] = 1
    target_pos.loc[trend_mode & bearish] = -1
    
    # 当 CI > 50 (震荡) 时，平仓? 还是保持?
    # 通常 Choppy 时不应持仓或减仓。这里选择平仓。
    # 所以 target_pos 默认为 0 已经包含了 CI >= 50 的情况
    
    df['pos'] = target_pos
    
    # 转化为 signal (diff)
    # 1 -> 1: 0
    # 0 -> 1: 1 (Open Long)
    # 1 -> 0: 0 (Close Long - handled by logic, but here we need signal format)
    # Signal format in this framework:
    # signal_long = 1 (Open), 0 (Close)
    # signal_short = -1 (Open), 0 (Close)
    
    # 构造 signal_long
    df['signal_long'] = np.nan
    df.loc[(df['pos'] == 1) & (df['pos'].shift(1) != 1), 'signal_long'] = 1
    df.loc[(df['pos'] != 1) & (df['pos'].shift(1) == 1), 'signal_long'] = 0
    
    # 构造 signal_short
    df['signal_short'] = np.nan
    df.loc[(df['pos'] == -1) & (df['pos'].shift(1) != -1), 'signal_short'] = -1
    df.loc[(df['pos'] != -1) & (df['pos'].shift(1) == -1), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    
    # 去重
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'ci', 'ema', 'pos', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20, 25, 30]
    return [[p] for p in periods]
