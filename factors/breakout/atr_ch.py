"""
ATR通道突破策略 (ATR Channel)

原理:
基于平均真实波幅(ATR)构建动态通道。
通道中轨为收盘价均线，上下轨为中轨±N倍ATR。
价格突破上轨时做多，突破下轨时做空。
ATR通道能自适应市场波动率变化。

时间周期推荐:
- 4H: n=10-20, multiplier=2-3
- 12H: n=15-30, multiplier=2-3

参数范围:
- n (周期): [10, 15, 20, 25, 30]
- multiplier (ATR倍数): [2, 2.5, 3]
"""

from cta_api.function import *

def signal(df, para=[20, 2], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, ATR倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    multiplier = para[1]

    # 计算ATR
    df['tr'] = df['high'] - df['low']
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    # 计算通道中轨
    df['middle_band'] = df['close'].rolling(window=period, min_periods=1).mean()

    # 计算通道上下轨
    df['upper_band'] = df['middle_band'] + multiplier * df['atr']
    df['lower_band'] = df['middle_band'] - multiplier * df['atr']

    # 做多信号: 价格突破上轨
    condition1 = df['close'] > df['upper_band'].shift(1)
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格回落到中轨
    condition1 = df['close'] < df['middle_band']
    condition2 = df['close'].shift(1) >= df['middle_band'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格突破下轨
    condition1 = df['close'] < df['lower_band'].shift(1)
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格升到中轨
    condition1 = df['close'] > df['middle_band']
    condition2 = df['close'].shift(1) <= df['middle_band'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tr', 'atr', 'middle_band', 'upper_band', 'lower_band', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    - ATR倍数: 2, 2.5, 3
    """
    periods = [10, 15, 20, 25, 30]
    multipliers = [2, 2.5, 3]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])

    return para_list
