"""
OBV能量潮策略

原理:
OBV(On-Balance Volume)累加成交量，上涨日加正下跌日加负。
OBV上升确认上涨趋势，下降确认下跌趋势。
用于确认价格趋势的成交量验证。

时间周期推荐:
- 1H: n=5-20
- 4H: n=10-30
- 12H: n=20-50
- 24H: n=20-100

参数n范围: [5, 10, 20, 30, 50]
"""

from cta_api.function import *

def signal(df, para=[10], proportion=1, leverage_rate=1):
    period = para[0]

    df['obv'] = df['volume'].copy()

    direction = np.where(df['close'] > df['close'].shift(1), 1, -1)
    df['obv'] = df['volume'] * direction

    df['obv_ma'] = df['obv'].rolling(window=period, min_periods=1).mean()

    df['obv_signal'] = np.where(df['obv'] > df['obv_ma'], 1, -1)
    prev_obv_signal = df['obv_signal'].shift(1)

    buy_signal = (df['obv_signal'] == 1) & (prev_obv_signal != 1)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['obv_signal'] == -1, 'signal_long'] = 0

    sell_signal = (df['obv_signal'] == -1) & (prev_obv_signal != -1)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['obv_signal'] == 1, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['obv', 'obv_ma', 'obv_signal', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [5, 10, 20, 30, 50]
    return [[period] for period in periods]
