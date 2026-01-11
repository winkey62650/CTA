"""
均值回归通道策略

原理:
围绕均值构建通道，价格触及通道边界时反向交易。
价格触及下轨买入，触及上轨卖出。
适用于震荡行情的区间交易。

时间周期推荐:
- 1H: n=10-30
- 4H: n=15-50
- 12H: n=20-60
- 24H: n=30-100

参数n范围: [10, 15, 20, 30, 40, 50, 60]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 2.0], proportion=1, leverage_rate=1):
    period = para[0]
    std_multiplier = para[1]

    df['mean'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['std'] = df['close'].rolling(window=period, min_periods=1).std()

    df['upper'] = df['mean'] + std_multiplier * df['std']
    df['lower'] = df['mean'] - std_multiplier * df['std']

    touch_lower = (df['close'] <= df['lower']) & (df['close'].shift(1) > df['lower'].shift(1))
    df.loc[touch_lower, 'signal_long'] = 1
    df.loc[df['close'] >= df['mean'], 'signal_long'] = 0

    touch_upper = (df['close'] >= df['upper']) & (df['close'].shift(1) < df['upper'].shift(1))
    df.loc[touch_upper, 'signal_short'] = -1
    df.loc[df['close'] <= df['mean'], 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['mean', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 15, 20, 30, 40, 50, 60]
    std_multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]

    para_list = []
    for period in periods:
        for std_mult in std_multipliers:
            para_list.append([period, std_mult])
    return para_list
