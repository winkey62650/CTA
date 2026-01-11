"""
随机震荡指标策略 (Stochastic Oscillator)

原理:
随机震荡指标结合%K、%D和慢速%K(Slow Stochastic)。
%K = (收盘价 - N周期最低价) / (最高价 - 最低价) * 100
%D = %K的M周期平滑
Slow %K = %K的N2周期平滑
%K上穿%D时做多，下穿时做空。
Fast %K < 20超卖，> 80超买。

时间周期推荐:
- 1H: n=5-14
- 4H: n=14

参数范围:
- n (周期): [5, 7, 14]
- d (平滑%D周期): [3, 5]
"""

from cta_api.function import *

def signal(df, para=[14, 3], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, %D平滑周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    d_period = para[1]

    # 计算最高最低价
    high_n = df['high'].rolling(window=period, min_periods=1).max()
    low_n = df['low'].rolling(window=period, min_periods=1).min()

    # 计算%K
    df['k_fast'] = (df['close'] - low_n) / (high_n - low_n) * 100

    # 计算%D (%K的平滑)
    df['d'] = df['k_fast'].rolling(window=d_period, min_periods=1).mean()

    # 计算Slow %K (更平滑的%K)
    df['k_slow'] = df['k_fast'].rolling(window=period, min_periods=1).mean()

    # 做多信号: %K上穿%D (超卖反弹或趋势启动)
    condition1 = df['k_fast'] > df['d']
    condition2 = df['k_fast'].shift(1) <= df['d'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: %K下穿%D或Fast %K < 20(超卖区域)
    condition1 = df['k_fast'] < df['d']
    condition2 = df['k_fast'].shift(1) >= df['d'].shift(1)
    condition3 = df['k_fast'] < 20
    df.loc[(condition1 | condition2 | condition3) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: %K下穿%D (超买回调或趋势启动)
    condition1 = df['k_fast'] < df['d']
    condition2 = df['k_fast'].shift(1) >= df['d'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: %K上穿%D或Fast %K > 80(超买区域)
    condition1 = df['k_fast'] > df['d']
    condition2 = df['k_fast'].shift(1) <= df['d'].shift(1)
    condition3 = df['k_fast'] > 80
    df.loc[(condition1 | condition2 | condition3) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['k_fast', 'd', 'k_slow', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 7, 14
    - %D平滑周期: 3, 5
    """
    periods = [5, 7, 14]
    d_periods = [3, 5]

    para_list = []
    for period in periods:
        for d in d_periods:
            para_list.append([period, d])

    return para_list
