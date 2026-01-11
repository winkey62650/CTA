"""
Aroon指标策略 (Aroon Oscillator)

原理:
Aroon由三条线组成:Aroon Up, Aroon Down和Aroon Oscillator。
Up线和Down线分别衡量上升和下降趋势，Oscillator是它们的平均线。
Aroon Oscillator上穿Up线时做多，下穿Down线时做空。

时间周期推荐:
- 4H: n=25
- 12H: n=25

参数范围:
- n (周期): [20, 25, 30, 35]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[25], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算最高价和最低价
    high_periods = df['high'].rolling(window=period, min_periods=1)
    low_periods = df['low'].rolling(window=period, min_periods=1)

    # 计算Aroon Up (基于最高价)
    df['aroon_up'] = high_periods.max()

    # 计算Aroon Down (基于最低价)
    df['aroon_down'] = low_periods.min()

    # 计算Aroon Oscillator
    df['aroon_osc'] = (df['aroon_up'] + df['aroon_down']) / 2

    # 做多信号: Oscillator上穿Up线
    condition1 = df['aroon_osc'] > df['aroon_up'].shift(1)
    condition2 = df['aroon_osc'].shift(1) <= df['aroon_up'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: Oscillator回落到Up线
    condition1 = df['aroon_osc'] < df['aroon_up'].shift(1)
    condition2 = df['aroon_osc'].shift(1) >= df['aroon_up'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: Oscillator下穿Down线
    condition1 = df['aroon_osc'] < df['aroon_down'].shift(1)
    condition2 = df['aroon_osc'].shift(1) >= df['aroon_down'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: Oscillator回升到Down线
    condition1 = df['aroon_osc'] > df['aroon_down'].shift(1)
    condition2 = df['aroon_osc'].shift(1) <= df['aroon_down'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['aroon_up', 'aroon_down', 'aroon_osc', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 20, 25, 30, 35
    """
    periods = [20, 25, 30, 35]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
