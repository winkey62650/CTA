"""
心理线策略 (PSY Line)

原理:
PSY (Psychological Line) 统计过去N天内上涨天数的比例。
公式: PSY = (N日内上涨天数 / N) * 100
在币圈，极端情绪往往延续。
本策略采用趋势跟随逻辑：
- PSY > 50: 多头占优，做多
- PSY < 50: 空头占优，做空

参数:
- n: 周期 (推荐 12-24)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[12], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 判断上涨: Close > Prev Close
    is_up = (df['close'] > df['close'].shift(1)).astype(int)
    
    # 计算PSY
    df['psy'] = is_up.rolling(window=n).sum() / n * 100
    
    # 趋势逻辑
    # 上穿50做多
    condition1 = df['psy'] > 50
    condition2 = df['psy'].shift(1) <= 50
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    # 下穿50做空
    condition1 = df['psy'] < 50
    condition2 = df['psy'].shift(1) >= 50
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    # 平仓
    # 下穿50平多
    df.loc[condition1 & condition2, 'signal_long'] = 0
    # 上穿50平空
    c_cross_up = (df['psy'] > 50) & (df['psy'].shift(1) <= 50)
    df.loc[c_cross_up, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['psy', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 12, 14, 20, 24, 30]
    return [[p] for p in periods]
