"""
三均线系统策略 (Triple Moving Average)

原理:
使用短、中、长三条均线形成排列，判断趋势强度和方向。
多头排列(短>中>长)时做多，空头排列(短<中<长)时做空。
比双均线更稳定，减少假信号。

时间周期推荐:
- 4H: n=[5, 10, 20]
- 12H: n=[10, 20, 40]
- 24H: n=[20, 50, 100]

参数n范围: [5, 10, 20, 30, 40, 50, 60, 100, 150, 200]
"""

from cta_api.function import *

def signal(df, para=[10, 20, 50], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期周期, 中期周期, 长期周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    mid_period = para[1]
    long_period = para[2]

    # 计算三条均线
    df['ma_short'] = df['close'].rolling(window=short_period, min_periods=1).mean()
    df['ma_mid'] = df['close'].rolling(window=mid_period, min_periods=1).mean()
    df['ma_long'] = df['close'].rolling(window=long_period, min_periods=1).mean()

    # 多头排列: 短>中>长
    bull_alignment = (df['ma_short'] > df['ma_mid']) & (df['ma_mid'] > df['ma_long'])

    # 空头排列: 短<中<长
    bear_alignment = (df['ma_short'] < df['ma_mid']) & (df['ma_mid'] < df['ma_long'])

    # 排列变化判断
    prev_bull = bull_alignment.shift(1)
    prev_bear = bear_alignment.shift(1)

    # 做多信号: 从非多头变为多头排列
    df.loc[bull_alignment & ~prev_bull, 'signal_long'] = 1

    # 做多平仓: 多头排列破坏
    df.loc[~bull_alignment & prev_bull, 'signal_long'] = 0

    # 做空信号: 从非空头变为空头排列
    df.loc[bear_alignment & ~prev_bear, 'signal_short'] = -1

    # 做空平仓: 空头排列破坏
    df.loc[~bear_alignment & prev_bear, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ma_short', 'ma_mid', 'ma_long', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    三条均线的斐波那契比例组合
    """
    short_list = [5, 10, 15, 20, 25]
    mid_list = [10, 20, 30, 40, 50]
    long_list = [20, 50, 75, 100, 150]

    para_list = []
    for short in short_list:
        for mid in mid_list:
            for long in long_list:
                if short < mid < long:
                    para_list.append([short, mid, long])

    return para_list
