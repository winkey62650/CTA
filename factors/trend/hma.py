"""
赫尔移动平均策略 (Hull Moving Average - HMA)

原理:
HMA是一种快速响应的移动平均线，能有效减少滞后。
它使用加权移动平均和平方根周期来提高对价格变化的敏感度。
HMA上穿/下穿时产生买卖信号，适用于快速趋势跟踪。

时间周期推荐:
- 1H: n=5-15
- 4H: n=10-30

参数n范围: [5, 7, 10, 12, 15, 20, 25, 30, 40, 50]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 50], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期HMA周期, 长期HMA周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    long_period = para[1]

    # 计算HMA
    df['hma_short'] = calculate_hma(df['close'], short_period)
    df['hma_long'] = calculate_hma(df['close'], long_period)

    # 做多信号: 短期HMA上穿长期HMA
    condition1 = df['hma_short'] > df['hma_long']
    condition2 = df['hma_short'].shift(1) <= df['hma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 短期HMA下穿长期HMA
    condition1 = df['hma_short'] < df['hma_long']
    condition2 = df['hma_short'].shift(1) >= df['hma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 短期HMA下穿长期HMA
    condition1 = df['hma_short'] < df['hma_long']
    condition2 = df['hma_short'].shift(1) >= df['hma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 短期HMA上穿长期HMA
    condition1 = df['hma_short'] > df['hma_long']
    condition2 = df['hma_short'].shift(1) <= df['hma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['hma_short', 'hma_long', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def calculate_hma(series, period):
    """
    计算赫尔移动平均线
    HMA(n) = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    """
    half_period = int(period / 2)
    sqrt_period = int(np.sqrt(period))

    # 计算WMA
    wma_half = series.rolling(window=half_period, min_periods=1).mean()
    wma_full = series.rolling(window=period, min_periods=1).mean()

    # HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))
    hma_raw = 2 * wma_half - wma_full
    hma = hma_raw.rolling(window=sqrt_period, min_periods=1).mean()

    return hma


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 短期周期: 5, 7, 10, 12, 15, 20
    - 长期周期: 10, 15, 20, 25, 30, 40, 50
    - 短期 < 长期
    """
    short_periods = [5, 7, 10, 12, 15, 20]
    long_periods = [10, 15, 20, 25, 30, 40, 50]

    para_list = []
    for short in short_periods:
        for long in long_periods:
            if short < long:
                para_list.append([short, long])

    return para_list
