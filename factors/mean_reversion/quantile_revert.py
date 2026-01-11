"""
分位数回归策略 (Quantile Reversion)

原理:
计算价格在N周期内的分位数，当价格回到特定分位数时产生信号。
分位数范围0-25表示低位，75-100表示高位。
价格低于25分位数时做多(超卖回归)，高于75分位数时做空(超买回归)。
价格回到中值(50分位数)时平仓。

时间周期推荐:
- 1H: n=20-40
- 4H: n=40-60

参数范围:
- n (周期): [20, 30, 40, 50, 60, 80, 100]
- quantile (分位数): [0.2, 0.25, 0.75, 0.8]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[50, 0.25], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 分位数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    quantile = para[1]

    # 计算分位数
    df['quantile'] = df['close'].rolling(window=period, min_periods=1).quantile(quantile)

    # 做多信号: 价格低于下分位数(超卖)
    condition1 = df['close'] < df['quantile'].shift(1)
    condition2 = df['quantile'] <= 0.25
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回归中值(50分位数)
    condition1 = df['close'] >= 0.5
    condition2 = df['close'].shift(1) < 0.5
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格高于上分位数(超买)
    condition1 = df['close'] > df['quantile'].shift(1)
    condition2 = df['quantile'] >= 0.75
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回归中值(50分位数)
    condition1 = df['close'] <= 0.5
    condition2 = df['close'].shift(1) > 0.5
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['quantile', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 20, 30, 40, 50, 60, 80, 100
    - 分位数: 0.2, 0.25, 0.75, 0.8
    """
    periods = [20, 30, 40, 50, 60, 80, 100]
    quantiles = [0.2, 0.25, 0.75, 0.8]

    para_list = []
    for period in periods:
        for q in quantiles:
            para_list.append([period, q])

    return para_list
