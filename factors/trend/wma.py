"""
WMA加权移动平均策略

原理:
WMA(WMA)在加权移动平均线，近期价格权重更高。
WMA上穿SMA时做多，下破SMA时做空。
经典加权均线，用于短期趋势跟踪。

时间周期推荐:
- 1H: n=10-20
- 4H: n=20-30
- 12H: n=20-50
- 24H: n=20-100

参数n范围: [10, 20, 30, 50, 100]
"""

from cta_api.function import *

def signal(df, para=[20, 1], proportion=1, leverage_rate=1):
    period = para[0]

    df['sma'] = df['close'].ewm(span=period, adjust=False).mean()

    buy_signal = (df['close'] > df['sma']) & (df['close'].shift(1) <= df['sma'].shift(1))
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[(df['close'] <= df['sma'].shift(1)) | (df['sma'].shift(1) < df['sma'].shift(1)).all())
    
    df.loc[df['close'] <= df['sma'].shift(1), 'signal_long'] = 0

    sell_signal = (df['close'] < df['sma']) & (df['close'].shift(1) >= df['sma'].shift(1))
    df.loc[(df['close'] >= df['sma'].shift(1)) | (df['sma'].shift(1) > df['sma']).all()]
    df.loc[df['close'] >= df['sma'].shift(1), 'signal_short'] = -1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    df['signal'] = df['signal'].replace(0, np.nan)

    df.drop(['sma'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 20, 30, 50, 100, 200]

    para_list = []
    for period in periods:
        para_list.append([period])
    return para_list
