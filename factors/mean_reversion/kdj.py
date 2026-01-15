"""
随机指标策略 (KDJ / Stochastic)

原理:
KDJ是改进版的随机指标，包含%K、%D、%J三条线。
%K是未成熟随机值(类似RSI)，%D是%K的移动平均，%J是%K和2%D-3%D。
%K > %D时做多(超卖)，%K < %D时做空(超买)。
%J用于确认信号强度。

时间周期推荐:
- 1H: n=(9,3,3)
- 4H: n=(14,3,3)

参数范围:
- n (周期): [5, 7, 9, 14, 21]
- m (平滑%K): [3, 5]
"""

from cta_api.function import *

def signal(df, para=[9, 3, 3], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, %D平滑周期, %J参数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    m = para[1]
    j_factor = para[2]

    # 计算最高最低价
    high_n = df['high'].rolling(window=period, min_periods=1).max()
    low_n = df['low'].rolling(window=period, min_periods=1).min()

    # 计算%K (未成熟随机值)
    df['k_raw'] = (df['close'] - low_n) / (high_n - low_n) * 100

    # 计算%D (%K的平滑值)
    df['k'] = df['k_raw'].rolling(window=m, min_periods=1).mean()

    # 计算%J
    df['j'] = 3 * df['k'] - 2 * df['k'].shift(1)

    # 做多信号: %K上穿%D (超卖转超买)
    condition1 = df['k'] > df['j']
    condition2 = df['k'].shift(1) <= df['j'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: %K下穿%D或超买区平仓
    condition1 = df['k'] < df['j']
    condition2 = df['k'].shift(1) >= df['j'].shift(1)
    condition3 = df['k'] > 80  # 超买区域平仓
    df.loc[(condition1 | condition2 | condition3) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: %K下穿%D (超买转超卖)
    condition1 = df['k'] < df['j']
    condition2 = df['k'].shift(1) >= df['j'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: %K上穿%D或超卖区平仓
    condition1 = df['k'] > df['j']
    condition2 = df['k'].shift(1) <= df['j'].shift(1)
    condition3 = df['k'] < 20  # 超卖区域平仓
    df.loc[(condition1 | condition2 | condition3) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['k_raw', 'k', 'j', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 7, 9, 14, 21
    - %D平滑周期: 3, 5
    - %J参数: 3 (固定值)
    """
    periods = [5, 7, 9, 14, 21]
    ms = [3, 5]

    para_list = []
    for period in periods:
        for m in ms:
            para_list.append([period, m, 3])

    return para_list
