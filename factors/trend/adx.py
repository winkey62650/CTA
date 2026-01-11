"""
ADX平均方向指数策略

原理:
ADX衡量趋势强度，数值越大趋势越强。
ADX > 25为强趋势适合做多，ADX < 20为震荡市避免交易。
用于过滤震荡市中的假信号。

时间周期推荐:
- 1H: n=10-14
- 4H: n=14-14
- 12H: n=14-20
- 24H: n=14-30

参数n范围: [10, 14, 20]
"""

from cta_api.function import *

def signal(df, para=[14, 25], proportion=1, leverage_rate=1):
    period = para[0]
    adx_threshold = para[1]

    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'])
    close_low = np.abs(df['close'] - df['low'])

    df['tr'] = np.maximum.reduce([high_low, high_close, close_low], axis=1)

    df['dm_plus'] = df['tr'].where(df['tr'] > 0, df['tr'], -df['tr'])
    df['dm_minus'] = np.abs(df['dm_plus']) + np.abs(df['dm_minus'])

    df['tr'] = df['dm_plus'].rolling(window=period, min_periods=1).mean()
    df['dm_minus_smooth'] = df['dm_minus'].rolling(window=period, min_periods=1).mean()

    df['dx'] = (df['dm_plus'] + df['dm_minus_smooth']) / 2

    df['adx'] = df['dx'].rolling(window=period, min_periods=1).mean()

    df['trend_strength'] = df['adx']

    trend_filter = df['trend_strength'] >= adx_threshold

    prev_trend = trend_filter.shift(1)

    buy_signal = trend_filter & (~prev_trend) & (df['close'] > df['close'].shift(1))
    df.loc[buy_signal, 'signal_long'] = 1

    sell_signal = trend_filter & (~prev_trend) & (df['close'] < df['close'].shift(1))
    df.loc[sell_signal, 'signal_short'] = -1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'dm_plus', 'dm_minus', 'tr', 'dx', 'adx', 'trend_strength', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20]
    thresholds = [20, 25, 30, 35]

    para_list = []
    for period in periods:
        for threshold in thresholds:
            para_list.append([period, threshold])
    return para_list
