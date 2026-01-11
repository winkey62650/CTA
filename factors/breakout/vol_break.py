"""
成交量突破策略 (Volume Breakout)

原理:
基于成交量放大的价格突破策略。
当价格突破关键价位时，必须有成交量放大确认。
成交量放大 = 当前成交量 > N周期平均成交量的倍数。
这样可以过滤假突破，提高信号质量。

时间周期推荐:
- 4H: n=10-20, multiplier=1.5-2.5
- 12H: n=15-30, multiplier=1.5-2.5

参数范围:
- n (周期): [10, 15, 20, 25, 30]
- multiplier (成交量倍数): [1.5, 2, 2.5, 3]
"""

from cta_api.function import *

def signal(df, para=[20, 2], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 成交量倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    multiplier = para[1]

    # 计算成交量均线
    df['vol_ma'] = df['volume'].rolling(window=period, min_periods=1).mean()

    # 计算价格高低点
    df['price_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['price_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 计算成交量放大
    df['vol_surge'] = df['volume'] > df['vol_ma'] * multiplier

    # 做多信号: 价格突破新高且成交量放大
    condition1 = df['close'] > df['price_high'].shift(1)
    condition2 = df['vol_surge']
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回落或成交量萎缩
    condition1 = df['close'] < df['price_high'].shift(1)
    condition2 = df['vol_surge'].shift(1) & ~df['vol_surge']
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: 价格突破新低且成交量放大
    condition1 = df['close'] < df['price_low'].shift(1)
    condition2 = df['vol_surge']
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回升或成交量萎缩
    condition1 = df['close'] > df['price_low'].shift(1)
    condition2 = df['vol_surge'].shift(1) & ~df['vol_surge']
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['vol_ma', 'price_high', 'price_low', 'vol_surge', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    - 成交量倍数: 1.5, 2, 2.5, 3
    """
    periods = [10, 15, 20, 25, 30]
    multipliers = [1.5, 2, 2.5, 3]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])

    return para_list
