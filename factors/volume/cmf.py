"""
Chaikin Money Flow (资金流向指标)

原理:
CMF 结合了价格和成交量，衡量一定周期内的资金累积/派发情况。
CMF > 0: 资金流入，多头市场。
CMF < 0: 资金流出，空头市场。
策略: 0轴交叉。

参数:
- n: 周期 (推荐 20)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[20], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 1. Money Flow Multiplier
    # MFM = ((Close - Low) - (High - Close)) / (High - Low)
    #     = (2*Close - Low - High) / (High - Low)
    
    high_low = df['high'] - df['low']
    high_low = high_low.replace(0, 0.00001)
    
    mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / high_low
    
    # 2. Money Flow Volume
    mf_volume = mf_multiplier * df['volume']
    
    # 3. CMF = Sum(MFV, n) / Sum(Vol, n)
    df['cmf'] = mf_volume.rolling(window=n).sum() / df['volume'].rolling(window=n).sum()
    
    # 信号: 0轴交叉
    
    # 上穿0轴做多
    condition1 = df['cmf'] > 0
    condition2 = df['cmf'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    # 下穿0轴做空
    condition1 = df['cmf'] < 0
    condition2 = df['cmf'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    # 平仓
    df.loc[df['cmf'] < 0, 'signal_long'] = 0
    df.loc[df['cmf'] > 0, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['cmf', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [14, 20, 21, 30]
    return [[p] for p in periods]
