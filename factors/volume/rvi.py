"""
RVI策略 (Relative Volatility Index)

原理:
RVI基于波动率加权，衡量市场波动性。
RVI使用高低价差和收盘价差。
正向波动率RVI+ = (高价 - 收盘价) / (最高价 - 最低价)
负向波动率RVI- = (低价 - 收盘价) / (最高价 - 最低价)
RVI = RVI+ + RVI-
当RVI上穿基准线时做多，下穿时做空。
RVI值高表示高波动，低表示低波动。

时间周期推荐:
- 4H: n=10
- 12H: n=10

参数范围:
- n (周期): [5, 10, 15]
"""

from cta_api.function import *

def signal(df, para=[10], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算最高价
    high_period = df['high'].rolling(window=period, min_periods=1)

    # 计算正向和负向波动率
    df['pos_vri'] = (df['high'] - df['close']).where(high_period.max() - df['high'] >= 0, df['high'] - df['close']) / (high_period.max() - high_period.min())
    df['neg_vri'] = (df['low'] - df['close']).where(high_period.max() - df['low'] >= 0, df['low'] - df['close']) / (high_period.max() - high_period.min())

    # 计算RVI
    df['rvi'] = df['pos_vri'] + df['neg_vri']

    # 计算RVI基准
    df['rvi_ma'] = df['rvi'].rolling(window=period, min_periods=1).mean()

    # 做多信号: RVI上穿基准线
    condition1 = df['rvi'] > df['rvi_ma']
    condition2 = df['rvi'].shift(1) <= df['rvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: RVI回落到基准线
    condition1 = df['rvi'] < df['rvi_ma']
    condition2 = df['rvi'].shift(1) >= df['rvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: RVI下穿基准线
    condition1 = df['rvi'] < df['rvi_ma']
    condition2 = df['rvi'].shift(1) >= df['rvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: RVI回升到基准线
    condition1 = df['rvi'] > df['rvi_ma']
    condition2 = df['rvi'].shift(1) <= df['rvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['high', 'low', 'close', 'pos_vri', 'neg_vri', 'rvi', 'rvi_ma', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 10, 15
    """
    periods = [5, 10, 15]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
