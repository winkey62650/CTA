"""
单参数超级趋势策略 (Single Parameter SuperTrend)

原理:
SuperTrend 是基于ATR的趋势跟踪指标。
本策略固定倍数为3倍ATR（币圈常用），仅调整ATR周期。
上轨 = (High+Low)/2 + 3*ATR
下轨 = (High+Low)/2 - 3*ATR

参数:
- n: ATR周期 (推荐 10-50)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[10], proportion=1, leverage_rate=1):
    n = para[0]
    multiplier = 3.0
    
    # 计算ATR
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(window=n).mean()
    
    df['hl2'] = (df['high'] + df['low']) / 2
    df['basic_upper'] = df['hl2'] + multiplier * df['atr']
    df['basic_lower'] = df['hl2'] - multiplier * df['atr']
    
    # 计算Final Bands (需要遍历，较慢，改用向量化近似或Numba)
    # 这里使用简单的向量化逻辑模拟 SuperTrend 的翻转特性
    
    # 初始化
    df['final_upper'] = df['basic_upper']
    df['final_lower'] = df['basic_lower']
    df['super_trend'] = np.nan
    df['trend_dir'] = 1 # 1: Long, -1: Short
    
    # 由于SuperTrend的递归特性（当前值依赖前值），准确计算需要循环
    # 为保证效率，这里使用简化逻辑：
    # 当收盘价 > 上一次的Final Upper，趋势转多
    # 当收盘价 < 上一次的Final Lower，趋势转空
    # 趋势为多时，Lower band不降低；趋势为空时，Upper band不升高
    
    # 使用纯Python循环（Numba会更快，但为了兼容性先写Python，数据量不大时可接受）
    # 或者使用 cta_api.function 中的 Numba 加速（如果有）
    # 这里直接写一个简单的循环
    
    close = df['close'].values
    basic_upper = df['basic_upper'].values
    basic_lower = df['basic_lower'].values
    final_upper = np.zeros(len(df))
    final_lower = np.zeros(len(df))
    trend = np.zeros(len(df)) # 1 up, -1 down
    
    curr_trend = 1
    curr_upper = basic_upper[0]
    curr_lower = basic_lower[0]
    
    for i in range(1, len(df)):
        if np.isnan(basic_upper[i]):
            continue
            
        # Update Final Upper
        if basic_upper[i] < curr_upper or close[i-1] > curr_upper:
            curr_upper = basic_upper[i]
        else:
            curr_upper = curr_upper
            
        # Update Final Lower
        if basic_lower[i] > curr_lower or close[i-1] < curr_lower:
            curr_lower = basic_lower[i]
        else:
            curr_lower = curr_lower
            
        # Update Trend
        if curr_trend == 1:
            if close[i] < curr_lower:
                curr_trend = -1
        else:
            if close[i] > curr_upper:
                curr_trend = 1
                
        final_upper[i] = curr_upper
        final_lower[i] = curr_lower
        trend[i] = curr_trend
        
    df['trend'] = trend
    
    # 生成信号
    condition_long = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    condition_short = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    
    df.loc[condition_long, 'signal_long'] = 1
    df.loc[condition_short, 'signal_long'] = 0
    
    df.loc[condition_short, 'signal_short'] = -1
    df.loc[condition_long, 'signal_short'] = 0
    
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'atr', 'hl2', 'basic_upper', 'basic_lower', 'final_upper', 'final_lower', 'trend', 'super_trend', 'trend_dir', 'signal_long', 'signal_short'], axis=1, inplace=True, errors='ignore')
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20, 30, 50, 60]
    return [[p] for p in periods]
