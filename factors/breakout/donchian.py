"""
Donchian通道突破策略

原理:
唐奇安通道使用N周期最高价和最低价形成通道。
价格突破N日新高做多，突破N日新低做空。
经典趋势跟踪策略，捕捉长期趋势。

时间周期推荐:
- 1H: n=20
- 4H: n=20
- 12H: n=55
- 24H: n=100

参数n范围: [10, 20, 30, 50, 75, 100]
"""

from cta_api.function import *

def signal(df, para=[20, 1.0], proportion=1, leverage_rate=1):
    period = para[0]

    df['highest_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['lowest_low'] = df['low'].rolling(window=period, min_periods=1).min()

    buy_signal = (df['close'] > df['highest_high'].shift(1))
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['close'] < df['highest_high'].shift(2), 'signal_long'] = 0

    sell_signal = (df['close'] < df['lowest_low'].shift(1))
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['close'] > df['lowest_low'].shift(2), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['highest_high', 'lowest_low', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 20, 30, 50, 75, 100]
    multiplier = 1.0

    para_list = [[period, multiplier] for period in periods]
    return para_list
