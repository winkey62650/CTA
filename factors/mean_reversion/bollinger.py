"""
标准布林带策略 (Bollinger Bands - Mean Reversion)

原理:
布林带由中轨(SMA)、上轨(+2σ)、下轨(-2σ)组成。
价格触及下轨为超卖买入信号，触及上轨为超买卖出信号。
适用于震荡行情中的均值回归交易。

时间周期推荐:
- 1H: n=10-20
- 4H: n=15-30
- 12H: n=20-40
- 24H: n=20-60

参数n范围: [10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[20, 2.0], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [均线周期, 标准差倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    std_dev = para[1]

    # 计算中轨
    df['middle_band'] = df['close'].rolling(window=period, min_periods=1).mean()

    # 计算标准差
    df['std_dev'] = df['close'].rolling(window=period, min_periods=1).std()

    # 计算上下轨
    df['upper_band'] = df['middle_band'] + std_dev * df['std_dev']
    df['lower_band'] = df['middle_band'] - std_dev * df['std_dev']

    # 买入信号: 价格从下轨反弹 (下穿转为上穿)
    # 条件1: 当前价格低于或等于下轨
    # 条件2: 前一根K线价格低于下轨
    # 条件3: 当前价格开始回升 (close > low或close > 前一close)
    prev_close = df['close'].shift(1)
    prev_lower_band = df['lower_band'].shift(1)

    # 更简单的逻辑: 价格下破下轨后回升
    touch_lower = (df['close'] <= df['lower_band']) & (prev_close > prev_lower_band)

    # 卖出信号: 价格上破上轨后回落
    prev_upper_band = df['upper_band'].shift(1)
    touch_upper = (df['close'] >= df['upper_band']) & (prev_close < prev_upper_band)

    # 做多信号
    df.loc[touch_lower, 'signal_long'] = 1

    # 做多平仓: 回到中轨或触及上轨
    back_to_middle = df['close'] >= df['middle_band']
    df.loc[back_to_middle, 'signal_long'] = 0

    # 做空信号
    df.loc[touch_upper, 'signal_short'] = -1

    # 做空平仓: 回到中轨或触及下轨
    df.loc[back_to_middle, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['middle_band', 'std_dev', 'upper_band', 'lower_band', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    周期从10到60，步长5
    标准差倍数从1.5到3.0，步长0.5
    """
    periods = list(range(10, 61, 5))  # 10, 15, 20, ..., 60
    std_devs = [1.5, 2.0, 2.5, 3.0]

    para_list = []
    for period in periods:
        for std in std_devs:
            para_list.append([period, std])

    return para_list
