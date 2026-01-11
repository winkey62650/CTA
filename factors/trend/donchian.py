"""
通道突破策略 (Donchian Channel)

原理:
Donchian通道由N周期内的最高价和最低价构成。
当价格突破N日新高时做多，跌破N日新低时做空。
这是经典的海龟交易法则突破策略，适用于趋势性行情。

时间周期推荐:
- 4H: n=20-60
- 12H: n=20-100
- 24H: n=20-100

参数n范围: [10, 20, 30, 40, 50, 60, 80, 100]
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [通道周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算Donchian通道
    df['donchian_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['donchian_low'] = df['low'].rolling(window=period, min_periods=1).min()
    df['donchian_middle'] = (df['donchian_high'] + df['donchian_low']) / 2

    # 做多信号: 价格突破通道上沿
    condition1 = df['close'] > df['donchian_high'].shift(1)
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破通道中值
    condition1 = df['close'] < df['donchian_middle']
    condition2 = df['close'].shift(1) >= df['donchian_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格跌破通道下沿
    condition1 = df['close'] < df['donchian_low'].shift(1)
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格升破通道中值
    condition1 = df['close'] > df['donchian_middle']
    condition2 = df['close'].shift(1) <= df['donchian_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['donchian_high', 'donchian_low', 'donchian_middle', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 通道周期: 10, 20, 30, 40, 50, 60, 80, 100
    """
    periods = [10, 20, 30, 40, 50, 60, 80, 100]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
