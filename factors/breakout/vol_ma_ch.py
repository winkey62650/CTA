"""
成交量均线突破策略 (Volume MA Breakout)

原理:
基于成交量均线(CMA)的突破策略。
成交量突破N周期均线时，表明资金流入增加。
配合价格确认，产生买卖信号。
CMA = 成交量的移动平均。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (周期): [10, 15, 20, 25, 30]
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

    # 计算成交量均线
    df['vol_ma'] = df['volume'].rolling(window=period, min_periods=1).mean()

    # 计算价格突破
    df['price_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['price_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 计算成交量突破方向
    df['vol_up'] = df['volume'] > df['vol_ma']
    df['vol_down'] = df['volume'] < df['vol_ma']

    # 做多信号: 成交量突破均线且价格突破新高
    condition1 = df['vol_up']
    condition2 = df['close'] > df['price_high'].shift(1)
    condition3 = df['vol_up'].shift(1) == False
    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 1

    # 做多平仓信号: 成交量回落均线
    condition1 = df['vol_down']
    condition2 = df['vol_up'].shift(1) == True
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 成交量突破均线且价格突破新低
    condition1 = df['vol_down']
    condition2 = df['close'] < df['price_low'].shift(1)
    condition3 = df['vol_down'].shift(1) == False
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1

    # 做空平仓信号: 成交量回升均线
    condition1 = df['vol_up']
    condition2 = df['vol_down'].shift(1) == True
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['vol_ma', 'price_high', 'price_low', 'vol_up', 'vol_down', 'signal_long', 'signal_short'], axis=1, inplace=True)

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
