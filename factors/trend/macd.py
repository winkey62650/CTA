"""
标准MACD策略 (Moving Average Convergence Divergence)

原理:
MACD由快线(DIF)、慢线(DEA)和柱状图(MACD)组成。
DIF上穿DEA时做多，下穿时做空。
MACD柱状图可以判断动能强弱。
这是最经典的技术指标之一。

时间周期推荐:
- 4H: params=(12,26,9)
- 12H: params=(12,26,9)
- 24H: params=(12,26,9)

参数范围:
- fast_period: 5-15 (推荐12)
- slow_period: 20-30 (推荐26)
- signal_period: 5-12 (推荐9)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

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

    # 计算DIF (快线)
    df['dif'] = df['ema_fast'] - df['ema_slow']

    # 计算DEA (信号线)
    df['dea'] = df['dif'].ewm(span=signal_period, adjust=False).mean()

    # 计算MACD柱状图
    df['macd_hist'] = (df['dif'] - df['dea']) * 2

    # 做多信号: DIF上穿DEA
    condition1 = df['dif'] > df['dea']
    condition2 = df['dif'].shift(1) <= df['dea'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: DIF下穿DEA
    condition1 = df['dif'] < df['dea']
    condition2 = df['dif'].shift(1) >= df['dea'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: DIF下穿DEA
    condition1 = df['dif'] < df['dea']
    condition2 = df['dif'].shift(1) >= df['dea'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: DIF上穿DEA
    condition1 = df['dif'] > df['dea']
    condition2 = df['dif'].shift(1) <= df['dea'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

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

    参数组合:
    - 快线周期: 5, 8, 12, 15
    - 慢线周期: 20, 24, 26, 30
    - 信号线周期: 5, 7, 9, 12
    - 快线 < 慢线
    """
    fast_periods = [5, 8, 12, 15]
    slow_periods = [20, 24, 26, 30]
    signal_periods = [5, 7, 9, 12]

    para_list = []
    for fast in fast_periods:
        for slow in slow_periods:
            for sig in signal_periods:
                if fast < slow:
                    para_list.append([fast, slow, sig])

    return para_list
