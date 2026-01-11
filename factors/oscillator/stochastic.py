"""
Stochastic随机指标策略

原理:
随机指标(Stochastic)比较收盘价与N周期高低点的相对位置。
%K上穿%D线且都低于超卖线时买入，下穿且都高于超买线时卖出。
适用于捕捉趋势转折点。

时间周期推荐:
- 1H: n=(14,3,3)
- 4H: n=(14,3,3)
- 12H: n=(14,3,3)
- 24H: n=(14,3,3)

参数n范围: [(14,3,3), (14,5,3), (20,5,3)]
"""

from cta_api.function import *

def signal(df, para=[14, 3, 3], proportion=1, leverage_rate=1):
    k_period = para[0]
    d_period = para[1]
    smooth_period = para[2]
    oversold = 20
    overbought = 80

    df['lowest_low'] = df['low'].rolling(window=k_period, min_periods=1).min()
    df['highest_high'] = df['high'].rolling(window=k_period, min_periods=1).max()
    df['%k'] = 100 * (df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low'])

    df['%d'] = df['%k'].rolling(window=d_period, min_periods=1).mean()

    df['%d_slow'] = df['%d'].rolling(window=smooth_period, min_periods=1).mean()

    buy_signal = (df['%k'] > df['%d']) & (df['%k'] < oversold)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[(df['%k'] >= 80) | (df['%d'] >= df['%d_slow']), 'signal_long'] = 0

    sell_signal = (df['%k'] < df['%d']) & (df['%k'] > overbought)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[(df['%k'] <= 20) | (df['%d'] <= df['%d_slow']), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['lowest_low', 'highest_high', '%k', '%d', '%d_slow', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    k_periods = [14, 14, 20]
    d_periods = [3, 3, 5]
    smooth_periods = [3, 3, 5]

    para_list = []
    for k in k_periods:
        for d in d_periods:
            for s in smooth_periods:
                para_list.append([k, d, s])
    return para_list
