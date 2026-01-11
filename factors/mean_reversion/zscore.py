"""
Z-Score标准化策略

原理:
Z-Score将价格标准化到标准正态分布。
Z < -2为超卖(买入)，Z > 2为超买(卖出)。
捕捉价格异常值，均值回归策略。

时间周期推荐:
- 1H: n=20-40
- 4H: n=30-60
- 12H: n=40-80
- 24H: n=50-150

参数n范围: [20, 30, 40, 50, 80]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 2.0, -2.0], proportion=1, leverage_rate=1):
    period = para[0]
    threshold = para[1]
    oversold = para[2]

    df['mean'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['std'] = df['close'].rolling(window=period, min_periods=1).std()

    df['z_score'] = (df['close'] - df['mean']) / df['std']

    buy_signal = (df['z_score'] < oversold) & (df['z_score'].shift(1) >= oversold)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['z_score'] >= -threshold, 'signal_long'] = 0

    sell_signal = (df['z_score'] > threshold) & (df['z_score'].shift(1) <= threshold)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['z_score'] <= 2, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['mean', 'std', 'z_score', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [20, 30, 40, 50, 80]
    thresholds = [2.0, 2.5, 3.0]

    para_list = []
    for period in periods:
        for threshold in thresholds:
            para_list.append([period, threshold])
    return para_list
