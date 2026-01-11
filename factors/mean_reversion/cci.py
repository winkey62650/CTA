"""
商品通道指数策略 (Commodity Channel Index - CCI)

原理:
CCI用于衡量价格偏离移动平均的程度。
CCI = (TP - MA) / (0.015 * 平均绝对偏差)
其中TP = (最高价 + 最低价 + 收盘价) / 3
CCI在-100到+100之间波动，+100以上超买，-100以下超卖。
CCI上穿100时做多，下穿-100时做空。

时间周期推荐:
- 1H: n=14-20
- 4H: n=14-20

参数范围:
- n (周期): [10, 14, 20]
- overbought (超买线): [100, 150]
- oversold (超卖线): [-100, -150]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[14, 100, -100], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 超买线, 超卖线]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    overbought = para[1]
    oversold = para[2]

    # 计算TP (典型价格)
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3

    # 计算移动平均
    df['tp_ma'] = df['tp'].rolling(window=period, min_periods=1).mean()

    # 计算平均绝对偏差
    df['mad'] = (df['tp'] - df['tp_ma']).abs().rolling(window=period, min_periods=1).mean()

    # 计算CCI
    df['cci'] = (df['tp'] - df['tp_ma']) / (0.015 * df['mad'])

    # 做多信号: CCI上穿超卖线
    condition1 = df['cci'] > oversold
    condition2 = df['cci'].shift(1) <= oversold
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: CCI下穿超买线
    condition1 = df['cci'] < overbought
    condition2 = df['cci'].shift(1) >= overbought
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: CCI下穿超买线
    condition1 = df['cci'] < overbought
    condition2 = df['cci'].shift(1) <= overbought
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: CCI上穿超卖线
    condition1 = df['cci'] > oversold
    condition2 = df['cci'].shift(1) >= oversold
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tp', 'tp_ma', 'mad', 'cci', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 14, 20
    - 超买线: 100, 150
    - 超卖线: -100, -150
    """
    periods = [10, 14, 20]
    overboughts = [100, 150]
    oversolds = [-100, -150]

    para_list = []
    for period in periods:
        for over in overboughts:
            for over in oversolds:
                para_list.append([period, over, over])

    return para_list
