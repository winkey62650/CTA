"""
均值突破策略 (Mean Breakout)

原理:
基于均线(MA)的突破策略。
当价格突破N周期均线时，产生趋势信号。
价格上穿均线时做多，下穿均线时做空。
均线突破是最基础的趋势跟踪策略。

时间周期推荐:
- 1H: n=5-10
- 4H: n=10-25
- 12H: n=20-40

参数n范围: [5, 10, 15, 20, 25, 30, 40, 50]
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算均线
    df['ma'] = df['close'].rolling(window=period, min_periods=1).mean()

    # 做多信号: 价格上穿均线
    condition1 = df['close'] > df['ma'].shift(1)
    condition2 = df['close'].shift(1) <= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格下穿均线
    condition1 = df['close'] < df['ma']
    condition2 = df['close'].shift(1) >= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格下穿均线
    condition1 = df['close'] < df['ma'].shift(1)
    condition2 = df['close'].shift(1) >= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格上穿均线
    condition1 = df['close'] > df['ma']
    condition2 = df['close'].shift(1) <= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ma', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 10, 15, 20, 25, 30, 40, 50
    """
    periods = [5, 10, 15, 20, 25, 30, 40, 50]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
