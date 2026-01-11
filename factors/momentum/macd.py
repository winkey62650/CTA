"""
标准MACD策略 (Moving Average Convergence Divergence)

原理:
MACD由快线(DIF)、慢线(DEA)、柱状图组成。
DIF上穿DEA且DIF>0时做多，DIF下穿DEA且DIF<0时做空。
经典趋势跟踪指标，适用于单边趋势行情。

时间周期推荐:
- 1H: (5,13,5)
- 4H: (8,17,9)
- 12H: (12,26,9)
- 24H: (12,26,9)

参数n范围: [(5,13,5), (8,17,9), (12,26,9)]
"""

from cta_api.function import *

def signal(df, para=[12, 26, 9], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [快线周期, 慢线周期, 信号线周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    fast_period = para[0]
    slow_period = para[1]
    signal_period = para[2]

    # 计算EMA
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

    # DIF线 (快线)
    df['dif'] = df['ema_fast'] - df['ema_slow']

    # DEA线 (信号线)
    df['dea'] = df['dif'].ewm(span=signal_period, adjust=False).mean()

    # MACD柱状图
    df['macd_hist'] = df['dif'] - df['dea']

    # 做多信号: DIF上穿DEA 且 DIF > 0
    prev_dif = df['dif'].shift(1)
    prev_dea = df['dea'].shift(1)

    golden_cross = (df['dif'] > df['dea']) & (prev_dif <= prev_dea)
    df.loc[golden_cross & (df['dif'] > 0), 'signal_long'] = 1

    # 做多平仓: DIF下穿DEA 或 DIF < 0
    df.loc[(df['dif'] < df['dea']) | (df['dif'] < 0), 'signal_long'] = 0

    # 做空信号: DIF下穿DEA 且 DIF < 0
    death_cross = (df['dif'] < df['dea']) & (prev_dif >= prev_dea)
    df.loc[death_cross & (df['dif'] < 0), 'signal_short'] = -1

    # 做空平仓: DIF上穿DEA 或 DIF > 0
    df.loc[(df['dif'] > df['dea']) | (df['dif'] > 0), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ema_fast', 'ema_slow', 'dif', 'dea', 'macd_hist', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    经典MACD参数组合
    """
    para_list = [
        [5, 13, 5],
        [8, 17, 9],
        [12, 26, 9],
        [5, 35, 5],
        [12, 26, 9],
        [6, 19, 9],
        [8, 21, 7]
    ]

    # 扩展组合
    fast_periods = [5, 6, 8, 10, 12]
    slow_periods = [13, 19, 21, 26, 35]
    signal_periods = [5, 7, 9]

    for fast in fast_periods:
        for slow in slow_periods:
            for sig in signal_periods:
                if fast < slow:
                    para_list.append([fast, slow, sig])

    return para_list
