"""
海龟通道突破策略 (Turtle Channel)

原理:
基于海龟交易法则的双突破系统。
系统1: 20日突破（短期）
系统2: 55日突破（长期）
价格突破N日新高时做多，跌破N日新低时做空。
结合ATR进行止损管理。

时间周期推荐:
- 12H: n=[20, 55]
- 24H: n=[20, 55]

参数n范围: [15, 20, 25, 30, 40, 50, 55, 60]
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [突破周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算突破高低点
    df['turtle_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['turtle_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 计算ATR
    df['tr'] = df['high'] - df['low']
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    # 做多信号: 价格突破N日新高
    condition1 = df['close'] > df['turtle_high'].shift(1)
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破N日低点或ATR止损
    condition1 = df['close'] < df['turtle_low'].shift(1)
    condition2 = df['close'] < df['turtle_high'].shift(1) - 2 * df['atr'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: 价格跌破N日新低
    condition1 = df['close'] < df['turtle_low'].shift(1)
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格升破N日高点或ATR止损
    condition1 = df['close'] > df['turtle_high'].shift(1)
    condition2 = df['close'] > df['turtle_low'].shift(1) + 2 * df['atr'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['turtle_high', 'turtle_low', 'tr', 'atr', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 突破周期: 15, 20, 25, 30, 40, 50, 55, 60
    """
    periods = [15, 20, 25, 30, 40, 50, 55, 60]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
