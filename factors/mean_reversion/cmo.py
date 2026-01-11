"""
钱德动量摆动策略 (Chande Momentum Oscillator - CMO)

原理:
CMO比较上涨日和下跌日的价格动量。
CMO = (上涨日均值 - 下跌日均值) / (上涨日均值 + 下跌日均值) * 100
CMO在-100到+100之间波动，正值表示上涨动能，负值表示下跌动能。
CMO上穿0时做多，下穿0时做空。

时间周期推荐:
- 1H: n=10-20
- 4H: n=10-20

参数范围:
- n (周期): [10, 14, 20]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算价格变化
    df['price_change'] = df['close'].diff()

    # 上涨日
    df['up_day'] = df['price_change'].where(df['price_change'] > 0, 0)

    # 下跌日
    df['down_day'] = -df['price_change'].where(df['price_change'] < 0, 0)

    # 上涨日均值
    df['up_mean'] = df['up_day'].rolling(window=period, min_periods=1).mean()

    # 下跌日均值
    df['down_mean'] = df['down_day'].rolling(window=period, min_periods=1).mean()

    # 计算CMO
    df['cmo'] = (df['up_mean'] - df['down_mean']) / (df['up_mean'] + df['down_mean']) * 100

    # 做多信号: CMO上穿0
    condition1 = df['cmo'] > 0
    condition2 = df['cmo'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: CMO下穿0
    condition1 = df['cmo'] < 0
    condition2 = df['cmo'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: CMO下穿0
    condition1 = df['cmo'] < 0
    condition2 = df['cmo'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: CMO上穿0
    condition1 = df['cmo'] > 0
    condition2 = df['cmo'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['price_change', 'up_day', 'down_day', 'up_mean', 'down_mean', 'cmo',
             'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 14, 20
    """
    periods = [10, 14, 20]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
