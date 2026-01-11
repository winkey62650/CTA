"""
累积/派发线策略 (Accumulation/Distribution Line - A/D)

原理:
衡量买卖压力和累积趋势。
当日收盘价接近最高价时为买盘压力，A/D上升；
当日收盘价接近最低价时为卖盘压力，A/D下降。
A/D = (收盘价 - 开盘价) × (最高价 - 最低价) / (最高价 - 最低价)的绝对值
当日收盘价 > 开盘价且接近最高价时，买盘压力A/D上升；
当日收盘价 < 开盘价且接近最低价时，卖盘压力A/D下降。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (周期): [10, 15, 20, 25, 30]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算高低价
    df['high_low'] = df['high'] - df['low']

    # 计算收盘开盘价差
    df['cl'] = df['close'] - df['open']

    # 计算CLV (收盘离高低价的比例)
    df['clv'] = np.where(
        df['high_low'].shift(1) != 0,
        df['cl'] / df['high_low'].shift(1),
        df['cl'] / df['high_low'].shift(1)
    )

    # 计算A/D
    df['ad'] = df['clv'].cumsum()

    # 计算A/D均线
    df['ad_ma'] = df['ad'].rolling(window=period, min_periods=1).mean()

    # 计算价格突破
    df['price_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['price_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 做多信号: A/D上穿均线且价格突破新高
    condition1 = df['ad'] > df['ad_ma']
    condition2 = df['close'] > df['price_high'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: A/D下穿均线
    condition1 = df['ad'] < df['ad_ma']
    condition2 = df['ad'].shift(1) >= df['ad_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: A/D下穿均线且价格突破新低
    condition1 = df['ad'] < df['ad_ma']
    condition2 = df['close'] < df['price_low'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: A/D上穿均线
    condition1 = df['ad'] > df['ad_ma']
    condition2 = df['ad'].shift(1) <= df['ad_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['high_low', 'cl', 'clv', 'ad', 'ad_ma', 'price_high', 'price_low', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    """
    periods = [10, 15, 20, 25, 30]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
