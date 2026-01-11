"""
Chaikin震荡指标策略 (Chaikin Oscillator)

原理:
Chaikin震荡基于平均动向指数(ADX)。
CO = (EMA(ADL) - EMA(ADH)) - EMA(ADL)
正值表示强势市场，负值表示弱势市场。
CO上穿0时做多，下穿0时做空。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (周期): [10, 15, 20, 25]
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算最高价和最低价的EMA
    df['ema_high'] = df['high'].ewm(span=period, adjust=False).mean()
    df['ema_low'] = df['low'].ewm(span=period, adjust=False).mean()
    df['ema_close'] = df['close'].ewm(span=period, adjust=False).mean()

    # 计算动向线
    df['adl'] = df['ema_close'] - df['ema_low']
    df['adh'] = df['ema_high'] - df['ema_low']

    # 计算Chaikin震荡
    df['ch_osc'] = df['adl'].ewm(span=period, adjust=False).mean() - \
                  df['adh'].ewm(span=period, adjust=False).mean()

    # 做多信号: CO上穿0
    condition1 = df['ch_osc'] > 0
    condition2 = df['ch_osc'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: CO下穿0
    condition1 = df['ch_osc'] < 0
    condition2 = df['ch_osc'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: CO下穿0
    condition1 = df['ch_osc'] < 0
    condition2 = df['ch_osc'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: CO上穿0
    condition1 = df['ch_osc'] > 0
    condition2 = df['ch_osc'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ema_high', 'ema_low', 'ema_close', 'adl', 'adh', 'ch_osc', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25
    """
    periods = [10, 15, 20, 25]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
