"""
HMA均值回归策略 (HMA Mean Reversion)

原理:
使用赫尔移动平均(HMA)计算均值，价格回归到HMA时产生信号。
HMA是一种快速响应的均线，能减少滞后。
价格低于HMA时做多(超卖反弹)，高于HMA时做空(超买回调)。
价格回归到HMA时平仓。

时间周期推荐:
- 1H: n=5-20
- 4H: n=10-30

参数范围:
- hma_period (HMA周期): [5, 7, 10, 15, 20]
- std_multiplier (标准差倍数): [0.5, 1, 1.5, 2]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[10, 1.0], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [HMA周期, 标准差倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    hma_period = para[0]
    std_multiplier = para[1]

    # 计算HMA
    half_period = int(hma_period / 2)
    wma_half = df['close'].rolling(window=half_period, min_periods=1).mean()
    df['hma'] = wma_half.shift(1)

    # 计算HMA带
    df['hma_upper'] = df['hma'] + std_multiplier * df['close'].rolling(window=hma_period, min_periods=1).std()
    df['hma_lower'] = df['hma'] - std_multiplier * df['close'].rolling(window=hma_period, min_periods=1).std()

    # 做多信号: 价格下穿HMA下轨(超卖反弹)
    condition1 = df['close'] < df['hma_lower']
    condition2 = df['close'].shift(1) >= df['hma_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回归HMA
    condition1 = df['close'] >= df['hma']
    condition2 = df['close'].shift(1) < df['hma']
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格上穿HMA上轨(超买回调)
    condition1 = df['close'] > df['hma_upper']
    condition2 = df['close'].shift(1) <= df['hma_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回归HMA
    condition1 = df['close'] <= df['hma']
    condition2 = df['close'].shift(1) > df['hma']
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['hma', 'hma_upper', 'hma_lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - HMA周期: 5, 7, 10, 15, 20
    - 标准差倍数: 0.5, 1, 1.5, 2
    """
    periods = [5, 7, 10, 15, 20]
    stds = [0.5, 1, 1.5, 2]

    para_list = []
    for period in periods:
        for std in stds:
            para_list.append([period, std])

    return para_list
