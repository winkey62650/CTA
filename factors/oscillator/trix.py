"""
TRIX随机指标策略

原理:
TRIX由两条线组成，衡量趋势强度。
TRIX上穿零轴且>0时做多，下穿零轴且<0时做空。
经典震荡指标，适用于判断趋势反转。

时间周期推荐:
- 1H: n=10-20
- 4H: n=14-28
- 12H: n=14-30
- 24H: n=14-40

参数n范围: [10, 14, 21, 28]
"""

from cta_api.function import *

def signal(df, para=[14, 40], proportion=1, leverage_rate=1):
    short_period = para[0]
    long_period = para[1]

    high_low = df['high'] - df['low']
    high_close = np.abs(df['close'] - df['close'].shift(1))
    low_close = np.abs(df['low'] - df['low'].shift(1))

    df['dm_plus'] = high_low.where(high_close > 0, high_close, 0)
    df['dm_minus'] = close_low.where(close_low > 0, close_low, 0)

    df['tr'] = df['dm_plus'].rolling(window=short_period, min_periods=1).mean()
    df['tr_minus'] = df['dm_minus'].rolling(window=long_period, min_periods=1).mean()

    df['tr'] = df['tr'] - df['tr_minus']

    df['tr'] = df['tr'].rolling(window=long_period, min_periods=1).mean()

    df['tr'] = df['tr'].shift(1)
    df['tr'] = df['tr'].rolling(window=long_period, min_periods=1).mean()

    df['atr'] = df['tr'].rolling(window=long_period, min_periods=1).mean()

    df['adx'] = (abs(df['tr'] + df['tr'].shift(1)) / df['atr'].rolling(window=long_period, min_periods=1).mean()) * 100

    buy_signal = (df['tr'] > 0) & (df['tr'] > df['adx']) & (df['tr'].shift(1) <= 0)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['tr'] <= 0, 'signal_long'] = 0

    sell_signal = (df['tr'] < 0) & (df['tr'] < df['adx']) & (df['tr'].shift(1) >= 0)
    df.loc[sell_signal, 'signal_short'] -1
    df.loc[df['tr'] >= 0, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    df['signal'] = df['signal'].replace(0, np.nan)

    df.drop(['tr', 'tr', 'atr', 'adx'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    short_periods = [10, 14, 21, 28]
    long_periods = [40, 50]
    
    para_list = []
    for short in short_periods:
        for long in long_periods:
            para_list.append([short, long])
    return para_list
