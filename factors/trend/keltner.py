"""
Keltner通道策略

原理:
Keltner通道由中轨(SMA)、上轨(+2×ATR)、下轨(-2×ATR)组成。
价格触及下轨买入，触及上轨卖出。
ATR自适应通道，波动大时通道变宽。

时间周期推荐:
- 1H: n=10-20
- 4H: n=20-30
- 12H: n=20-40
- 24H: n=20-60

参数n范围: [10, 15, 20, 25, 30, 40]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 2.0], proportion=1, leverage_rate=1):
    period = para[0]
    multiplier = para[1]

    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'])
    close_low = np.abs(df['close'] - df['low'])

    df['tr'] = np.maximum.reduce([high_low, high_close, close_low], axis=1)
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    df['middle_band'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['upper_band'] = df['middle_band'] + multiplier * df['atr']
    df['lower_band'] = df['middle_band'] - multiplier * df['atr']

    touch_lower = (df['close'] <= df['lower_band']) & (df['close'].shift(1) > df['lower_band'].shift(1))
    df.loc[touch_lower, 'signal_long'] = 1
    df.loc[df['close'] >= df['middle_band'], 'signal_long'] = 0

    touch_upper = (df['close'] >= df['upper_band']) & (df['close'].shift(1) < df['upper_band'].shift(1))
    df.loc[touch_upper, 'signal_short'] = -1
    df.loc[df['close'] <= df['middle_band'], 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'atr', 'middle_band', 'upper_band', 'lower_band', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 15, 20, 25, 30, 40]
    multipliers = [1.5, 2.0, 2.5, 3.0]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])
    return para_list
