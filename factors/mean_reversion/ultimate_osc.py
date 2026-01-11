"""
最终震荡指标策略 (Ultimate Oscillator - UO)

原理:
UO是加权综合震荡指标，结合了短期、中期、长期三个时间框架。
计算三个时间框架的震荡值，并加权平均。
UO在0到100之间波动，接近0表示中性，接近100表示超买。
UO上穿50时做多，下穿50时做空。

时间周期推荐:
- 1H: n=[7,14,28]
- 4H: n=[7,14,28]

参数范围:
- n (短/中/长期): [7, 14, 21, 28]
"""

from cta_api.function import *

def signal(df, para=[7, 14, 28], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期周期, 中期周期, 长期周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    mid_period = para[1]
    long_period = para[2]

    # 计算典型价格
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3

    # 计算短期振荡
    df['bp_short'] = df['close'].rolling(window=short_period, min_periods=1).min()
    df['sp_short'] = df['close'].rolling(window=short_period, min_periods=1).max()
    df['uo_short'] = 100 * (df['tp'] - df['bp_short']) / (df['sp_short'] - df['bp_short'])

    # 计算中期振荡
    df['bp_mid'] = df['close'].rolling(window=mid_period, min_periods=1).min()
    df['sp_mid'] = df['close'].rolling(window=mid_period, min_periods=1).max()
    df['uo_mid'] = 100 * (df['tp'] - df['bp_mid']) / (df['sp_mid'] - df['bp_mid'])

    # 计算长期振荡
    df['bp_long'] = df['close'].rolling(window=long_period, min_periods=1).min()
    df['sp_long'] = df['close'].rolling(window=long_period, min_periods=1).max()
    df['uo_long'] = 100 * (df['tp'] - df['bp_long']) / (df['sp_long'] - df['bp_long'])

    # 计算加权平均UO
    df['uo'] = (4 * df['uo_short'] + 2 * df['uo_mid'] + df['uo_long']) / 7

    # 做多信号: UO上穿50
    condition1 = df['uo'] > 50
    condition2 = df['uo'].shift(1) <= 50
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: UO下穿50
    condition1 = df['uo'] < 50
    condition2 = df['uo'].shift(1) >= 50
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: UO下穿50
    condition1 = df['uo'] < 50
    condition2 = df['uo'].shift(1) >= 50
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: UO上穿50
    condition1 = df['uo'] > 50
    condition2 = df['uo'].shift(1) <= 50
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tp', 'bp_short', 'sp_short', 'uo_short', 'bp_mid', 'sp_mid', 'uo_mid',
             'bp_long', 'sp_long', 'uo_long', 'uo', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 短期: 7, 14, 21
    - 中期: 14, 21, 28
    - 长期: 21, 28
    """
    short_periods = [7, 14, 21]
    mid_periods = [14, 21, 28]
    long_periods = [21, 28]

    para_list = []
    for short in short_periods:
        for mid in mid_periods:
            for long in long_periods:
                if short < mid < long:
                    para_list.append([short, mid, long])

    return para_list
