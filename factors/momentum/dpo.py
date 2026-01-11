"""
DPO指标策略 (Detrended Price Oscillator)

原理:
DPO消除价格的长期趋势，只保留短期波动。
DPO = EMA(收盘价, 短周期) - EMA(收盘价, 长周期)
正值表示价格高于长期均线，负值表示低于。
DPO上穿0时做多，下穿0时做空。

时间周期推荐:
- 1H: short=5-10, long=20-30
- 4H: short=10-15, long=20-35

参数范围:
- short_period (短周期): [5, 10, 15]
- long_period (长周期): [20, 25, 30]
"""

from cta_api.function import *

def signal(df, para=[10, 20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短周期, 长周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    long_period = para[1]

    # 计算短期EMA
    df['ema_short'] = df['close'].ewm(span=short_period, adjust=False).mean()

    # 计算长期EMA
    df['ema_long'] = df['close'].ewm(span=long_period, adjust=False).mean()

    # 计算DPO
    df['dpo'] = df['ema_short'] - df['ema_long']

    # 做多信号: DPO > 0 (价格高于趋势)
    condition1 = df['dpo'] > 0
    condition2 = df['dpo'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: DPO回落到0
    condition1 = df['dpo'] < 0
    condition2 = df['dpo'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: DPO < 0 (价格低于趋势)
    condition1 = df['dpo'] < 0
    condition2 = df['dpo'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: DPO回升到0
    condition1 = df['dpo'] > 0
    condition2 = df['dpo'].shift(1) <= 0
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ema_short', 'ema_long', 'dpo', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 短周期: 5, 10, 15
    - 长周期: 20, 25, 30
    """
    short_periods = [5, 10, 15]
    long_periods = [20, 25, 30]

    para_list = []
    for short in short_periods:
        for long in long_periods:
            if short < long:
                para_list.append([short, long])

    return para_list
