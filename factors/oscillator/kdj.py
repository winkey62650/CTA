"""
KDJ随机指标策略

原理:
KDJ由%K(随机指标)、%D(K值平滑)、%J(%K的偏离)三条线组成。
%K上穿%D线且%K<20时买入，%K下穿%D线且%K>80时卖出。
经典震荡指标，用于捕捉趋势转折。

时间周期推荐:
- 1H: n=(9,3,3)
- 4H: n=(9,3,3)
- 12H: n=(9,3,3)
- 24H: n=(9,3,3)

参数n范围: [(9,3,3)]
"""

from cta_api.function import *

def signal(df, para=[9, 3, 3], proportion=1, leverage_rate=1):
    k_period = para[0]
    d_period = para[1]
    j_period = para[2]

    df['lowest_low'] = df['low'].rolling(window=k_period, min_periods=1).min()
    df['highest_high'] = df['high'].rolling(window=k_period, min_periods=1).max()

    df['%r'] = 100 * (df['close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low'])

    df['%k'] = df['%r'].rolling(window=d_period, min_periods=1).mean()
    df['%d'] = df['%k'].rolling(window=d_period, min_periods=1).mean()

    df['%j'] = 3 * df['%k'] - 2 * df['%d']

    df['kdj_k_signal'] = np.where(df['%k'] < 20, 1, np.where(df['%k'] > 80, -1, 0))

    buy_signal = (df['%k'] < df['%d']) & (df['%k'].shift(1) >= df['%d'].shift(1))
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['%k'] >= df['%d'], 'signal_long'] = 0

    sell_signal = (df['%k'] > df['%d']) & (df['%k'].shift(1) <= df['%d'].shift(1))
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['%k'] <= df['%d'], 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['lowest_low', 'highest_high', '%r', '%k', '%d', '%j', 'kdj_k_signal', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    k_periods = [9, 9, 14, 20]
    d_periods = [3, 3, 5]
    j_periods = [3, 3, 5]

    para_list = []
    for k in k_periods:
        for d in d_periods:
            for j in j_periods:
                para_list.append([k, d, j])
    return para_list
