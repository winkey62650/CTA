"""
Force Index (强力指数)

原理:
Force Index 由 Alexander Elder 提出，结合了价格变动幅度和成交量。
FI = (Close - Close_prev) * Volume
本策略使用 EMA 平滑后的 FI。
FI > 0: 买方力量主导 (做多)
FI < 0: 卖方力量主导 (做空)

参数:
- n: 平滑周期 (推荐 2-13)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[13], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 1. Raw Force Index
    # FI = Change * Volume
    change = df['close'].diff(1)
    fi_raw = change * df['volume']
    
    # 2. Smoothed Force Index (EMA)
    df['fi'] = fi_raw.ewm(span=n, adjust=False).mean()
    
    # 信号: 0轴交叉
    
    # 上穿0轴做多
    condition1 = df['fi'] > 0
    condition2 = df['fi'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    # 下穿0轴做空
    condition1 = df['fi'] < 0
    condition2 = df['fi'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    # 平仓
    df.loc[df['fi'] < 0, 'signal_long'] = 0
    df.loc[df['fi'] > 0, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['fi', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [2, 13, 20, 26]
    return [[p] for p in periods]
