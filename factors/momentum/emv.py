"""
简便运动指标策略 (Ease of Movement - EMV)

原理:
EMV结合价格变化率和成交量的箱体。
EMV = (价格变动 / 价格变动范围) * 成交量
价格变动大且成交量大时EMV值大。
EMV上穿0时做多，下穿0时做空。

时间周期推荐:
- 4H: n=14
- 12H: n=14

参数范围:
- n (周期): [10, 14, 20]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算最高价和最低价的移动平均
    df['high_ma'] = df['high'].rolling(window=period).mean()
    df['low_ma'] = df['low'].rolling(window=period).mean()

    # 计算价格变动
    df['price_move'] = df['high'] - df['low']
    df['price_range'] = df['high_ma'] - df['low_ma']

    # 计算箱体
    df['box_ratio'] = df['price_move'] / (df['price_range'] * df['volume'] + 0.0001)

    # 计算EMV
    df['emv'] = df['box_ratio'].rolling(window=period, min_periods=1).sum()

    # 做多信号: EMV > 0
    condition1 = df['emv'] > 0
    condition2 = df['emv'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: EMV回落到0
    condition1 = df['emv'] < 0
    condition2 = df['emv'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: EMV下穿0
    condition1 = df['emv'] < 0
    condition2 = df['emv'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: EMV上穿0
    condition1 = df['emv'] > 0
    condition2 = df['emv'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['high_ma', 'low_ma', 'price_move', 'price_range', 'box_ratio', 'emv', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 14, 20
    """
    periods = [10, 14, 20]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
