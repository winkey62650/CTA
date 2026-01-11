"""
海龟交易法则 (Turtle Trading System)

原理:
经典的趋势跟踪系统，使用双突破系统。
系统1: 20日突破（短期系统）
系统2: 55日突破（长期系统）
价格突破N日新高做多，突破N日新低做空。
同时使用ATR进行仓位管理和止损。

时间周期推荐:
- 12H: n=[20, 55]
- 24H: n=[20, 55]

参数n范围: [20, 55] (经典参数，也可调整为其他值)
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [突破周期] (20或55)
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算突破高低点
    df['turtle_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['turtle_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 计算ATR用于止损
    df['atr'] = df['high'] - df['low']
    df['atr'] = df['atr'].rolling(window=period, min_periods=1).mean()

    # 做多信号: 价格突破N日新高
    condition1 = df['close'] > df['turtle_high'].shift(1)
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破N日低点或2倍ATR止损
    condition1 = df['close'] < df['turtle_low'].shift(1)
    condition2 = df['close'] < df['turtle_high'].shift(1) - 2 * df['atr'].shift(1)
    df.loc[condition1 | condition2, 'signal_long'] = 0

    # 做空信号: 价格跌破N日新低
    condition1 = df['close'] < df['turtle_low'].shift(1)
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格升破N日高点或2倍ATR止损
    condition1 = df['close'] > df['turtle_high'].shift(1)
    condition2 = df['close'] > df['turtle_low'].shift(1) + 2 * df['atr'].shift(1)
    df.loc[condition1 | condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['turtle_high', 'turtle_low', 'atr', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 经典海龟参数: 20 (系统1), 55 (系统2)
    - 其他常用参数: 10, 15, 30, 40, 60
    """
    periods = [10, 15, 20, 30, 40, 55, 60]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
