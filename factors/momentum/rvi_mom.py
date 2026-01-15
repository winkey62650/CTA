"""
相对活力指数 (RVI Momentum)

原理:
RVI (Relative Vigor Index) 类似于随机指标，但它使用收盘价相对于开盘价的位置，而不是相对于最低价的位置。
RVI = SMA(Close-Open, n) / SMA(High-Low, n)
用于测量上涨/下跌的内在动力。

参数:
- n: 平滑周期 (推荐 10)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[10], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 核心公式
    # 为了减少噪音，通常会对分子分母做简单的平滑
    # 这里使用简单的SMA
    
    num = df['close'] - df['open']
    denom = df['high'] - df['low']
    
    # 避免除以0
    denom = denom.replace(0, 0.00001)
    
    rvi = num.rolling(window=n).mean() / denom.rolling(window=n).mean()
    
    # 信号线: 4周期对称加权移动平均 (SWMA) 或简单 SMA(4)
    # 这里用 SMA(4) 近似
    signal_line = rvi.rolling(window=4).mean()
    
    df['rvi'] = rvi
    df['rvi_signal'] = signal_line
    
    # 金叉做多
    condition1 = df['rvi'] > df['rvi_signal']
    condition2 = df['rvi'].shift(1) <= df['rvi_signal'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    # 死叉做空
    condition1 = df['rvi'] < df['rvi_signal']
    condition2 = df['rvi'].shift(1) >= df['rvi_signal'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    # 平仓
    df.loc[condition1 & condition2, 'signal_long'] = 0
    df.loc[condition1 & condition2, 'signal_short'] = 0 # 覆盖上面的-1? 不，顺序很重要
    # 修正逻辑：
    # 金叉: 平空开多
    # 死叉: 平多开空
    
    # 重写信号逻辑
    df['signal_long'] = np.nan
    df['signal_short'] = np.nan
    
    # Long Entry / Short Exit
    c_long = (df['rvi'] > df['rvi_signal']) & (df['rvi'].shift(1) <= df['rvi_signal'].shift(1))
    df.loc[c_long, 'signal_long'] = 1
    df.loc[c_long, 'signal_short'] = 0
    
    # Short Entry / Long Exit
    c_short = (df['rvi'] < df['rvi_signal']) & (df['rvi'].shift(1) >= df['rvi_signal'].shift(1))
    df.loc[c_short, 'signal_short'] = -1
    df.loc[c_short, 'signal_long'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['rvi', 'rvi_signal', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [5, 10, 14, 20, 30]
    return [[p] for p in periods]
