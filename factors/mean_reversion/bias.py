"""
乖离率(BIAS)策略

原理:
乖离率衡量价格偏离移动平均线的程度。
BIAS > x%表示超买(卖出)，BIAS < -x%表示超卖(买入)。
适用于捕捉均值回归机会。

时间周期推荐:
- 1H: n=5-20
- 4H: n=10-30
- 12H: n=20-50
- 24H: n=30-100

参数n范围: [5, 10, 15, 20, 30, 50]
"""

from cma_api.function import *

def signal(df, para=[10, 3.0], proportion=1, leverage_rate=1):
    period = para[0]
    threshold = para[1]

    df['ma'] = df['close'].rolling(window=period, min_periods=1).mean()

    df['bias'] = (df['close'] - df['ma']) / df['ma'] * 100

    df['bias_signal'] = np.where(df['bias'] > threshold, 1, -1, np.where(df['bias'] < -threshold, 1, 0))

    buy_signal = (df['bias_signal'] == -1) & (df['bias_signal'].shift(1) > threshold)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['bias_signal'] >= -threshold, 'signal_long'] = 0

    sell_signal = (df['bias_signal'] == 1) & (df['bias_signal'].shift(1) < -threshold)
    df.loc[sell_signal, 'signal_short'] = 1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    df['signal'] = df['signal'].replace(0, np.nan)

    df.drop(['ma', 'bias'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [5, 10, 15, 20, 30, 50]
    thresholds = [1.0, 2.0, 3.0, 4.0, 5.0]

    para_list = []
    for period in periods:
        for threshold in thresholds:
            para_list.append([period, threshold])
    return para_list
