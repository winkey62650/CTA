"""
假突破过滤策略 (Fake Breakout Filter)

原理:
过滤假突破信号，减少无效交易。
当价格突破后，必须在N根K线内保持在突破方向。
如果价格很快反转，则认为是假突破，取消信号。
这样可以减少震荡市的无效交易。

时间周期推荐:
- 4H: n=3-10
- 12H: n=5-15

参数范围:
- n (确认周期): [3, 5, 7, 10, 15]
"""

from cta_api.function import *

def signal(df, para=[5], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [确认周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    confirm_period = para[0]

    # 计算价格突破
    df['high_breakout'] = df['high'].rolling(window=confirm_period, min_periods=1).max()
    df['low_breakout'] = df['low'].rolling(window=confirm_period, min_periods=1).min()

    # 计算突破方向
    df['upward_breakout'] = df['close'] > df['high_breakout'].shift(1)
    df['downward_breakout'] = df['close'] < df['low_breakout'].shift(1)

    # 做多信号: 向上突破
    condition1 = df['upward_breakout']
    condition2 = df['upward_breakout'].shift(1) == False
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 向下突破或确认期过后反转
    condition1 = df['downward_breakout']
    condition2 = df['close'] < df['high_breakout'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: 向下突破
    condition1 = df['downward_breakout']
    condition2 = df['downward_breakout'].shift(1) == False
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 向上突破或确认期过后反转
    condition1 = df['upward_breakout']
    condition2 = df['close'] > df['low_breakout'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['high_breakout', 'low_breakout', 'upward_breakout', 'downward_breakout', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 确认周期: 3, 5, 7, 10, 15
    """
    periods = [3, 5, 7, 10, 15]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
