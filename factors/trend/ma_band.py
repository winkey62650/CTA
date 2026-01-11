"""
多重均线带策略 (MA Band)

原理:
使用多条均线形成通道，价格在通道内运行。
当价格突破通道上沿时做多，突破通道下沿时做空。
多条均线可以过滤假突破，提高信号质量。

时间周期推荐:
- 4H: n=5-40
- 12H: n=10-80

参数n范围: [5, 10, 15, 20, 30, 40, 50, 60, 80, 100]
"""

from cta_api.function import *

def signal(df, para=[20, 30, 40], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [均线1周期, 均线2周期, 均线3周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    ma1_period = para[0]
    ma2_period = para[1]
    ma3_period = para[2]

    # 计算多条均线
    df['ma1'] = df['close'].rolling(window=ma1_period, min_periods=1).mean()
    df['ma2'] = df['close'].rolling(window=ma2_period, min_periods=1).mean()
    df['ma3'] = df['close'].rolling(window=ma3_period, min_periods=1).mean()

    # 计算通道上下沿（使用外层均线）
    df['band_upper'] = df[['ma1', 'ma2', 'ma3']].max(axis=1)
    df['band_lower'] = df[['ma1', 'ma2', 'ma3']].min(axis=1)

    # 做多信号: 价格突破通道上沿
    condition1 = df['close'] > df['band_upper']
    condition2 = df['close'].shift(1) <= df['band_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破通道中值
    condition1 = df['close'] < ((df['band_upper'] + df['band_lower']) / 2)
    condition2 = df['close'].shift(1) >= ((df['band_upper'] + df['band_lower']) / 2).shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格跌破通道下沿
    condition1 = df['close'] < df['band_lower']
    condition2 = df['close'].shift(1) >= df['band_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格升破通道中值
    condition1 = df['close'] > ((df['band_upper'] + df['band_lower']) / 2)
    condition2 = df['close'].shift(1) <= ((df['band_upper'] + df['band_lower']) / 2).shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ma1', 'ma2', 'ma3', 'band_upper', 'band_lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 均线1周期: 5, 10, 15, 20, 30
    - 均线2周期: 10, 20, 30, 40, 50
    - 均线3周期: 20, 30, 40, 50, 60, 80
    - 均线1 < 均线2 < 均线3
    """
    ma1_periods = [5, 10, 15, 20, 30]
    ma2_periods = [10, 20, 30, 40, 50]
    ma3_periods = [20, 30, 40, 50, 60, 80]

    para_list = []
    for ma1 in ma1_periods:
        for ma2 in ma2_periods:
            for ma3 in ma3_periods:
                if ma1 < ma2 and ma2 < ma3:
                    para_list.append([ma1, ma2, ma3])

    return para_list
