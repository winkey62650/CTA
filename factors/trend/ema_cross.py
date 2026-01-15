"""
指数双均线交叉策略 (EMA Cross)

原理:
指数移动平均线(EMA)赋予近期价格更高权重，比SMA更敏感。
短期EMA上穿长期EMA时做多，下穿时做空。
适用于快速响应的趋势行情。

时间周期推荐:
- 1H: n=5-20
- 4H: n=10-50
- 12H: n=20-100
- 24H: n=30-200

参数n范围: [5, 8, 12, 15, 20, 26, 34, 50, 60, 100, 150, 200]
"""

from cta_api.function import *

def signal(df, para=[12, 26], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期EMA周期, 长期EMA周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    long_period = para[1]

    # 计算EMA (pandas ewm, adjust=False使用标准EMA公式)
    df['factor_ema_short'] = df['close'].ewm(span=short_period, adjust=False).mean()
    df['factor_ema_long'] = df['close'].ewm(span=long_period, adjust=False).mean()

    # 做多信号: 短期EMA上穿长期EMA
    condition1 = df['factor_ema_short'] > df['factor_ema_long']
    condition2 = df['factor_ema_short'].shift(1) <= df['factor_ema_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号
    condition1 = df['factor_ema_short'] < df['factor_ema_long']
    condition2 = df['factor_ema_short'].shift(1) >= df['factor_ema_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 短期EMA下穿长期EMA
    condition1 = df['factor_ema_short'] < df['factor_ema_long']
    condition2 = df['factor_ema_short'].shift(1) >= df['factor_ema_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号
    condition1 = df['factor_ema_short'] > df['factor_ema_long']
    condition2 = df['factor_ema_short'].shift(1) <= df['factor_ema_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    # df.drop(['ema_short', 'ema_long', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df.drop(['signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合: 经典的MACD参数组合
    - (5, 13) - 快速响应
    - (8, 17) - 中等响应
    - (12, 26) - 标准MACD
    - (20, 50) - 稳健趋势
    """
    para_list = [
        [5, 13],
        [8, 17],
        [12, 26],
        [20, 50]
    ]

    # 扩展更多组合
    short_periods = [5, 8, 12, 15, 20]
    long_periods = [13, 17, 26, 34, 50]

    for short in short_periods:
        for long in long_periods:
            if short < long:
                para_list.append([short, long])

    return para_list
