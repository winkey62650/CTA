"""
CCI商品通道策略

原理:
CCI衡量价格偏离移动平均线的程度，标准化到±100范围内。
CCI < -100为超卖(买入)，CCI > 100为超买(卖出)。
适用于捕捉价格极值反转。

时间周期推荐:
- 1H: n=10-20
- 4H: n=14-20
- 12H: n=20-30
- 24H: n=20-40

参数n范围: [10, 14, 20, 30, 40]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[14, -100, 100], proportion=1, leverage_rate=1):
    period = para[0]
    oversold = para[1]
    overbought = para[2]

    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp'] = df['typical_price'].rolling(window=period, min_periods=1).mean()

    df['mean_deviation'] = np.abs(df['typical_price'] - df['tp']).rolling(window=period, min_periods=1).mean()

    df['cci'] = (df['typical_price'] - df['tp']) / (0.015 * df['mean_deviation'])

    buy_signal = (df['cci'] < oversold) & (df['cci'].shift(1) >= oversold)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['cci'] >= 50, 'signal_long'] = 0

    sell_signal = (df['cci'] > overbought) & (df['cci'].shift(1) <= overbought)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['cci'] <= -50, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['typical_price', 'tp', 'mean_deviation', 'cci', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20, 30, 40]
    oversold_levels = [-150, -120, -100]
    overbought_levels = [100, 120, 150]

    para_list = []
    for period in periods:
        for os in oversold_levels:
            for ob in overbought_levels:
                para_list.append([period, os, ob])
    return para_list
