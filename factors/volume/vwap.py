"""
VWAP成交量加权均价策略

原理:
VWAP(Volume Weighted Average Price)以成交量为权重计算平均价。
价格突破VWAP时做多，跌破VWAP时做空。
成交量确认的趋势更可靠。

时间周期推荐:
- 1H: n=20-50
- 4H: n=50-100
- 12H: n=100-200
- 24H: n=200-500

参数n范围: [20, 50, 100, 200]
"""

from cta_api.function import *

def signal(df, para=[50], proportion=1, leverage_rate=1):
    period = para[0]

    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['typical_price'] * df['volume']).rolling(window=period, min_periods=1).sum() / df['volume'].rolling(window=period, min_periods=1).sum()

    df['vwap_signal'] = np.where(df['close'] > df['vwap'], 1, -1)

    buy_signal = (df['vwap_signal'] == 1) & (df['vwap_signal'].shift(1) != 1)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['vwap_signal'] == -1, 'signal_long'] = 0

    sell_signal = (df['vwap_signal'] == -1) & (df['vwap_signal'].shift(1) != -1)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['vwap_signal'] == 1, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['typical_price', 'vwap', 'vwap_signal', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [20, 50, 100, 200]
    return [[period] for period in periods]
