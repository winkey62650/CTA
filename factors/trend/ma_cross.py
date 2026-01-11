"""
简单双均线交叉策略 (SMA Cross)

原理:
短期均线上穿长期均线时做多，下穿时做空。
这是最经典的趋势跟踪策略，适用于单边趋势行情。

时间周期推荐:
- 1H: n=5-20
- 4H: n=10-50
- 12H: n=20-100
- 24H: n=30-200

参数n范围: [5, 10, 15, 20, 30, 50, 60, 100, 150, 200]
"""

from cta_api.function import *

def signal(df, para=[20, 50], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期周期, 长期周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    long_period = para[1]

    # 计算短期和长期均线
    df['ma_short'] = df['close'].rolling(window=short_period, min_periods=1).mean()
    df['ma_long'] = df['close'].rolling(window=long_period, min_periods=1).mean()

    # 做多信号: 短期均线上穿长期均线
    condition1 = df['ma_short'] > df['ma_long']
    condition2 = df['ma_short'].shift(1) <= df['ma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 短期均线下穿长期均线
    condition1 = df['ma_short'] < df['ma_long']
    condition2 = df['ma_short'].shift(1) >= df['ma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 短期均线下穿长期均线
    condition1 = df['ma_short'] < df['ma_long']
    condition2 = df['ma_short'].shift(1) >= df['ma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 短期均线上穿长期均线
    condition1 = df['ma_short'] > df['ma_long']
    condition2 = df['ma_short'].shift(1) <= df['ma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ma_short', 'ma_long', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 短期周期: 5, 10, 15, 20, 30
    - 长期周期: 20, 50, 60, 100, 150, 200
    - 短期 < 长期
    """
    short_periods = [5, 10, 15, 20, 30]
    long_periods = [20, 50, 60, 100, 150, 200]

    para_list = []
    for short in short_periods:
        for long in long_periods:
            if short < long:
                para_list.append([short, long])

    return para_list
