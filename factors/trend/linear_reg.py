"""
线性回归线策略 (Linear Regression Trend Line)

原理:
对价格与时间进行线性回归，得到趋势线。
价格高于趋势线时做多，低于趋势线时做空。
当价格远离趋势线时，可能发生回归。

时间周期推荐:
- 12H: n=20-60
- 24H: n=30-100

参数n范围: [20, 30, 40, 50, 60, 80, 100]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[50], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [回归周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算线性回归趋势线
    df['reg_line'] = df['close'].rolling(window=period).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0] * (len(x)-1) + np.polyfit(range(len(x)), x, 1)[1],
        raw=False
    )

    # 计算标准差带
    df['std_dev'] = df['close'].rolling(window=period).std()
    df['upper_band'] = df['reg_line'] + df['std_dev']
    df['lower_band'] = df['reg_line'] - df['std_dev']

    # 做多信号: 价格突破上轨
    condition1 = df['close'] > df['upper_band']
    condition2 = df['close'].shift(1) <= df['upper_band'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破趋势线
    condition1 = df['close'] < df['reg_line']
    condition2 = df['close'].shift(1) >= df['reg_line'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格突破下轨
    condition1 = df['close'] < df['lower_band']
    condition2 = df['close'].shift(1) >= df['lower_band'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格升破趋势线
    condition1 = df['close'] > df['reg_line']
    condition2 = df['close'].shift(1) <= df['reg_line'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['reg_line', 'std_dev', 'upper_band', 'lower_band', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 回归周期: 20, 30, 40, 50, 60, 80, 100
    """
    periods = [20, 30, 40, 50, 60, 80, 100]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
