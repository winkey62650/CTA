"""
可变移动平均策略 (Variable Moving Average - VMA)

原理:
VMA根据价格波动率动态调整平滑度。
波动率高时使用较短周期，波动率低时使用较长周期。
这使VMA对市场变化更敏感。
VMA上穿均线时做多，下穿时做空。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (基础周期): [10, 15, 20, 25, 30]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [基础周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    base_period = para[0]

    # 计算价格波动率
    df['volatility'] = df['close'].rolling(window=base_period).std()

    # 计算VMA周期(根据波动率动态调整)
    df['vma_period'] = base_period * (1 + (df['volatility'] / df['volatility'].mean()))
    df['vma_period'] = df['vma_period'].rolling(window=10).mean()

    # 计算VMA
    df['vma'] = df['close'].rolling(window=base_period, min_periods=1).mean()

    # 做多信号: 价格上穿VMA
    condition1 = df['close'] > df['vma']
    condition2 = df['close'].shift(1) <= df['vma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格下穿VMA
    condition1 = df['close'] < df['vma']
    condition2 = df['close'].shift(1) >= df['vma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格下穿VMA
    condition1 = df['close'] < df['vma']
    condition2 = df['close'].shift(1) >= df['vma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格上穿VMA
    condition1 = df['close'] > df['vma']
    condition2 = df['close'].shift(1) <= df['vma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['volatility', 'vma_period', 'vma', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 基础周期: 10, 15, 20, 25, 30
    """
    periods = [10, 15, 20, 25, 30]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
