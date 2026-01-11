"""
价格通道回归策略 (Price Channel Regression)

原理:
计算N周期内的价格通道(最高、最低、平均)。
价格在通道内震荡，突破通道时产生趋势信号。
回归中值时平仓，捕获区间震荡。

时间周期推荐:
- 4H: n=20-40
- 12H: n=40-60

参数n范围: [20, 30, 40, 50, 60, 80]
"""

from cta_api.function import *

def signal(df, para=[40], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [通道周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算价格通道
    df['channel_high'] = df['high'].rolling(window=period).max()
    df['channel_low'] = df['low'].rolling(window=period).min()
    df['channel_middle'] = (df['channel_high'] + df['channel_low']) / 2

    # 做多信号: 价格突破通道上沿
    condition1 = df['close'] > df['channel_high'].shift(1)
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格回归通道中值
    condition1 = df['close'] < df['channel_middle']
    condition2 = df['close'].shift(1) >= df['channel_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格跌破通道下沿
    condition1 = df['close'] < df['channel_low'].shift(1)
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格回归通道中值
    condition1 = df['close'] > df['channel_middle']
    condition2 = df['close'].shift(1) <= df['channel_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['channel_high', 'channel_low', 'channel_middle', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 通道周期: 20, 30, 40, 50, 60, 80
    """
    periods = [20, 30, 40, 50, 60, 80]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
