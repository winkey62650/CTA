"""
Ichimoku云图策略

原理:
Ichimoku云图由转换线、基准线、滞后线、快线组成。
价格突破云图做多，跌破云图做空。
综合趋势系统，适合中长周期。

时间周期推荐:
- 1H: n=(9,26,52)
- 4H: n=(9,26,52)
- 12H: n=(9,26,52)
- 24H: n=(9,26,52)

参数n范围: [(9,26,52)]
"""

from cta_api.function import *

def signal(df, para=[9, 26, 52], proportion=1, leverage_rate=1):
    tenkan = para[0]
    kijun = para[1]
    senkou = para[2]

    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'])
    close_low = np.abs(df['close'] - df['low'])

    df['tr'] = np.maximum.reduce([high_low, high_close, close_low], axis=1)

    df['tenkan'] = (df['high'] + df['low']) / 2
    df['tenkan_lead'] = df['tenkan'].shift(tenkan)

    df['kijun'] = df['low'].rolling(window=kijun, min_periods=1).min()
    df['kijun_lead'] = df['kijun'].shift(kijun)

    df['senkou_a'] = (df['tenkan'] + df['tenkan_lead'] + df['kijun']) / 3
    df['senkou_b'] = (df['tenkan'] + df['tenkan_lead'] + df['kijun']) / 3
    df['senkou_a_lead'] = df['senkou_a'].shift(senkou)
    df['senkou_b_lead'] = df['senkou_b'].shift(senkou)

    df['cloud_top'] = np.maximum(df['senkou_a'], df['senkou_a_lead'])
    df['cloud_bottom'] = np.minimum(df['senkou_b'], df['senkou_b_lead'])

    df['close_above_cloud'] = df['close'] >= df['cloud_top'].shift(1)

    buy_signal = df['close_above_cloud'] & (~df['close_above_cloud'].shift(1))
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[(~df['close_above_cloud']), 'signal_long'] = 0

    sell_signal = df['close'] < df['cloud_bottom'].shift(1) & (~df['close'] < df['cloud_bottom'].shift(1))
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[(~df['close'] < df['cloud_bottom']), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'tenkan', 'tenkan_lead', 'kijun', 'kijun_lead', 'senkou_a', 'senkou_b', 'senkou_a_lead', 'senkou_b_lead', 'cloud_top', 'cloud_bottom', 'close_above_cloud', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    tenkan = [9, 9, 12]
    kijun = [26, 26, 52]
    senkou = [52, 52, 52]

    para_list = []
    for t in tenkan:
        for k in kijun:
            for s in senkou:
                para_list.append([t, k, s])
    return para_list
