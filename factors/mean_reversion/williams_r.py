"""
威廉指标策略 (Williams %R)

原理:
威廉指标%R用于衡量收盘价在N周期内相对位置。
%R = (最高价 - 收盘价) / (最高价 - 最低价) * -100
%R在-100到0之间波动，0为超买区域，-100为超卖区域。
%R上穿-20或下穿-80时产生信号。

时间周期推荐:
- 1H: n=7-14
- 4H: n=14

参数范围:
- n (周期): [5, 7, 9, 14, 21]
- overbought (超卖线): [-20, -25, -30]
- oversold (超买线): [-80, -75, -70]
"""

from cta_api.function import *

def signal(df, para=[14, -20, -80], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 超卖线, 超买线]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    overbought = para[1]
    oversold = para[2]

    # 计算威廉指标%R
    high_n = df['high'].rolling(window=period, min_periods=1).max()
    low_n = df['low'].rolling(window=period, min_periods=1).min()
    df['williams_r'] = (high_n - df['close']) / (high_n - low_n) * -100

    # 做多信号: %R上穿超买线(超卖转超买)
    condition1 = df['williams_r'] > oversold
    condition2 = df['williams_r'].shift(1) <= oversold
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: %R下穿超卖线
    condition1 = df['williams_r'] < overbought
    condition2 = df['williams_r'].shift(1) >= overbought
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: %R下穿超买线(超买转超卖)
    condition1 = df['williams_r'] < oversold
    condition2 = df['williams_r'].shift(1) <= oversold
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: %R上穿超买线
    condition1 = df['williams_r'] > overbought
    condition2 = df['williams_r'].shift(1) >= overbought
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['williams_r', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 7, 9, 14, 21
    - 超卖线: -20, -25, -30
    - 超买线: -80, -75, -70
    """
    periods = [5, 7, 9, 14, 21]
    overboughts = [-20, -25, -30]
    oversolds = [-80, -75, -70]

    para_list = []
    for period in periods:
        for ob in overboughts:
            for os in oversolds:
                para_list.append([period, ob, os])

    return para_list
