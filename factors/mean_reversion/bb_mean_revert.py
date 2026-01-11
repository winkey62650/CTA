"""
布林带均值回归策略 (Bollinger Bands Mean Reversion)

原理:
布林带由中轨(SMA)和上下轨(±2标准差)构成。
价格触及上轨时反向做空(超买)，触及下轨时反向做多(超卖)。
等待价格回归中轨时平仓。

时间周期推荐:
- 1H: n=10-15
- 4H: n=10-25

参数范围:
- n (周期): [10, 15, 20, 25, 30]
- std_dev (标准差倍数): [2, 2.5, 3]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 2], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 标准差倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    std_dev = para[1]

    # 计算布林带
    df['bb_middle'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['bb_std'] = df['close'].rolling(window=period, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + std_dev * df['bb_std']
    df['bb_lower'] = df['bb_middle'] - std_dev * df['bb_std']

    # 做多信号: 价格触及下轨
    condition1 = df['close'] <= df['bb_lower']
    condition2 = df['close'].shift(1) > df['bb_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回归中轨
    condition1 = df['close'] >= df['bb_middle']
    condition2 = df['close'].shift(1) < df['bb_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格触及上轨
    condition1 = df['close'] >= df['bb_upper']
    condition2 = df['close'].shift(1) < df['bb_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回归中轨
    condition1 = df['close'] <= df['bb_middle']
    condition2 = df['close'].shift(1) > df['bb_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['bb_middle', 'bb_std', 'bb_upper', 'bb_lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    - 标准差倍数: 2, 2.5, 3
    """
    periods = [10, 15, 20, 25, 30]
    std_devs = [2, 2.5, 3]

    para_list = []
    for period in periods:
        for std in std_devs:
            para_list.append([period, std])

    return para_list
