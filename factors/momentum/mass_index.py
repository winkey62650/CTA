"""
质量指数策略 (Mass Index)

原理:
质量指数衡量价格变化的质量，结合价格变化率。
MI = 价格变化率 * 成交量。
正值表示高动能伴随高成交量(强势)，负值表示低动能。
MI上穿0时做多，下穿0时做空。

时间周期推荐:
- 1H: n=5-15
- 4H: n=10-20

参数范围:
- n (周期): [5, 10, 15, 20]
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

    # 计算价格变化率
    df['price_change'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100

    # 计算平均成交量
    df['vol_ma'] = df['volume'].rolling(window=period, min_periods=1).mean()

    # 计算质量指数
    df['mass_index'] = df['price_change'] * (df['volume'] / df['vol_ma'])

    # 平滑MI
    df['mi'] = df['mass_index'].rolling(window=3, min_periods=1).mean()

    # 做多信号: MI > 0 (高质量上涨)
    condition1 = df['mi'] > 0
    condition2 = df['mi'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: MI回落到0
    condition1 = df['mi'] < 0
    condition2 = df['mi'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: MI下穿0 (低质量下跌)
    condition1 = df['mi'] < 0
    condition2 = df['mi'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: MI上穿0 (反转动能)
    condition1 = df['mi'] > 0
    condition2 = df['mi'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['price_change', 'vol_ma', 'mass_index', 'mi', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 10, 15, 20
    """
    periods = [5, 10, 15, 20]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
