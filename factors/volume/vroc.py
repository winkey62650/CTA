"""
Volume ROC (成交量变动率策略)

原理:
监控成交量和价格的同步变动。
当成交量和价格同时上涨时，视为有效突破（做多）。
当成交量上涨但价格下跌时，视为恐慌抛售（做空）。
使用 VROC (Volume Rate of Change) 和 PROC (Price Rate of Change) 判断。

参数:
- n: 周期 (推荐 14)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    n = para[0]
    
    # Volume ROC
    # VROC = (Vol - Vol_n) / Vol_n
    df['vroc'] = df['volume'].pct_change(n)
    
    # Price ROC
    df['proc'] = df['close'].pct_change(n)
    
    # 策略逻辑:
    # 1. 强力上涨: VROC > 0 且 PROC > 0 (量价齐升)
    condition_long = (df['vroc'] > 0) & (df['proc'] > 0)
    
    # 2. 强力下跌: VROC > 0 且 PROC < 0 (放量下跌)
    condition_short = (df['vroc'] > 0) & (df['proc'] < 0)
    
    # 信号转换
    # 这里使用简单的状态维持
    
    df['pos'] = 0
    df.loc[condition_long, 'pos'] = 1
    df.loc[condition_short, 'pos'] = -1
    
    # 如果 VROC < 0 (缩量)，保持之前的仓位? 还是平仓?
    # 缩量通常意味着趋势减弱，这里选择平仓 (pos=0)
    # 所以上面默认0已经处理了
    
    # 构造 signal
    df['signal_long'] = np.nan
    df.loc[(df['pos'] == 1) & (df['pos'].shift(1) != 1), 'signal_long'] = 1
    df.loc[(df['pos'] != 1) & (df['pos'].shift(1) == 1), 'signal_long'] = 0
    
    df['signal_short'] = np.nan
    df.loc[(df['pos'] == -1) & (df['pos'].shift(1) != -1), 'signal_short'] = -1
    df.loc[(df['pos'] != -1) & (df['pos'].shift(1) == -1), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['vroc', 'proc', 'pos', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [5, 10, 14, 20]
    return [[p] for p in periods]
