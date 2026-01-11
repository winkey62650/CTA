"""
Williams %R策略

原理:
威廉指标(Williams %R)测量收盘价在N周期高低点之间的位置。
%R <-80为超卖(买入)，%R > -20为超买(卖出)。
适用于震荡行情中的反转交易。

时间周期推荐:
- 1H: n=7-14
- 4H: n=7-14
- 12H: n=14-21
- 24H: n=14-28

参数n范围: [7, 10, 14, 21, 28]
"""

from cta_api.function import *

def signal(df, para=[14, -20, 80], proportion=1, leverage_rate=1):
    period = para[0]
    oversold = para[1]
    overbought = para[2]

    df['highest_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['lowest_low'] = df['low'].rolling(window=period, min_periods=1).min()

    df['williams_r'] = -100 * (df['highest_high'] - df['close']) / (df['highest_high'] - df['lowest_low'])

    buy_signal = (df['williams_r'] < oversold) & (df['williams_r'].shift(1) >= oversold)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['williams_r'] >= 50, 'signal_long'] = 0

    sell_signal = (df['williams_r'] > overbought) & (df['williams_r'].shift(1) <= overbought)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['williams_r'] <= -50, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['highest_high', 'lowest_low', 'williams_r', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [7, 10, 14, 21, 28]
    oversold_levels = [-20, -25, -30]
    overbought_levels = [80, 85, 90]

    para_list = []
    for period in periods:
        for os in oversold_levels:
            for ob in overbought_levels:
                para_list.append([period, os, ob])
    return para_list
