"""
MACD零轴策略 (MACD Zero Line)

原理:
仅使用DIF线与零轴的关系产生信号。
DIF上穿零轴时做多，下穿零轴时做空。
这是一种更简单的MACD变体，减少了信号频率。

时间周期推荐:
- 4H: params=(12,26)
- 12H: params=(12,26)
- 24H: params=(12,26)

参数范围:
- fast_period: 5-15 (推荐12)
- slow_period: 20-30 (推荐26)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[12, 26], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [快线周期, 慢线周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    fast_period = para[0]
    slow_period = para[1]

    # 计算EMA
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

    # 计算DIF
    df['dif'] = df['ema_fast'] - df['ema_slow']

    # 做多信号: DIF上穿零轴
    condition1 = df['dif'] > 0
    condition2 = df['dif'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: DIF下穿零轴
    condition1 = df['dif'] < 0
    condition2 = df['dif'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: DIF下穿零轴
    condition1 = df['dif'] < 0
    condition2 = df['dif'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: DIF上穿零轴
    condition1 = df['dif'] > 0
    condition2 = df['dif'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ema_fast', 'ema_slow', 'dif', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 快线周期: 5, 8, 12, 15
    - 慢线周期: 20, 24, 26, 30
    - 快线 < 慢线
    """
    fast_periods = [5, 8, 12, 15]
    slow_periods = [20, 24, 26, 30]

    para_list = []
    for fast in fast_periods:
        for slow in slow_periods:
            if fast < slow:
                para_list.append([fast, slow])

    return para_list
