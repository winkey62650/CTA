"""
T3移动平均线策略 (T3 Moving Average)

原理:
T3由Tim Tillson提出，比普通EMA更平滑且滞后更小。
它实际上是多重EMA的加权组合。
T3能够很好地过滤币圈的日内噪音，捕捉平滑趋势。

参数:
- n: 周期 (推荐 5-20)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[10], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据
    :param para: [周期]
    :return:
    """
    n = para[0]
    v_factor = 0.7  # 默认体积系数

    # T3计算需要6层EMA
    # 计算EMA的alpha
    # Pandas ewm use span=n, alpha=2/(n+1)
    
    e1 = df['close'].ewm(span=n, adjust=False).mean()
    e2 = e1.ewm(span=n, adjust=False).mean()
    e3 = e2.ewm(span=n, adjust=False).mean()
    e4 = e3.ewm(span=n, adjust=False).mean()
    e5 = e4.ewm(span=n, adjust=False).mean()
    e6 = e5.ewm(span=n, adjust=False).mean()

    c1 = -v_factor**3
    c2 = 3*v_factor**2 + 3*v_factor**3
    c3 = -6*v_factor**2 - 3*v_factor - 3*v_factor**3
    c4 = 1 + 3*v_factor + v_factor**3 + 3*v_factor**2

    df['t3'] = c1*e6 + c2*e5 + c3*e4 + c4*e3
    
    # 策略逻辑: 价格上穿T3做多，下穿做空
    # 也可以用 T3 斜率
    
    # 这里使用价格交叉
    condition1 = df['close'] > df['t3']
    condition2 = df['close'].shift(1) <= df['t3'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    condition1 = df['close'] < df['t3']
    condition2 = df['close'].shift(1) >= df['t3'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0
    
    condition1 = df['close'] < df['t3']
    condition2 = df['close'].shift(1) >= df['t3'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    condition1 = df['close'] > df['t3']
    condition2 = df['close'].shift(1) <= df['t3'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    
    # 去重
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['t3', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [5, 8, 10, 15, 20, 30]
    return [[p] for p in periods]
