"""
ATR均值回归策略 (ATR Mean Reversion)

原理:
使用ATR(平均真实波幅)计算均值带。
当价格突破ATR均线时产生趋势信号，回归时平仓。
ATR上方N倍或下方N倍时做多或做空。
ATR也用于止损管理。

时间周期推荐:
- 4H: n=14-20
- 12H: n=20-30

参数范围:
- n (周期): [10, 14, 20, 30]
- atr_multiplier: [1.5, 2, 2.5, 3]
"""

from cta_api.function import *

def signal(df, para=[20, 2], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, ATR倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    atr_multiplier = para[1]

    # 计算ATR
    df['tr'] = df['high'] - df['low']
    df['atr'] = df['tr'].abs().rolling(window=period, min_periods=1).mean()

    # 计算ATR均线带
    df['atr_upper'] = df['close'] + atr_multiplier * df['atr']
    df['atr_middle'] = df['close']
    df['atr_lower'] = df['close'] - atr_multiplier * df['atr']

    # 做多信号: 价格突破ATR上轨(趋势启动)
    condition1 = df['close'] > df['atr_upper']
    condition2 = df['close'].shift(1) <= df['atr_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回归中线或跌破下轨
    condition1 = df['close'] < df['atr_middle']
    condition2 = df['close'].shift(1) >= df['atr_middle'].shift(1)
    condition3 = df['close'] < df['atr_lower']
    df.loc[(condition1 | condition2 | condition3) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: 价格突破ATR下轨
    condition1 = df['close'] < df['atr_lower']
    condition2 = df['close'].shift(1) >= df['atr_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回归中线或升破上轨
    condition1 = df['close'] > df['atr_middle']
    condition2 = df['close'].shift(1) <= df['atr_middle'].shift(1)
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tr', 'atr', 'atr_upper', 'atr_middle', 'atr_lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 14, 20, 30
    - ATR倍数: 1.5, 2, 2.5, 3
    """
    periods = [10, 14, 20, 30]
    multipliers = [1.5, 2, 2.5, 3]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])

    return para_list
