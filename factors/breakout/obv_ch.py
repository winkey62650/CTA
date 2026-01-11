"""
OBV突破策略 (OBV Breakout)

原理:
基于能量潮(OBV)的突破策略。
OBV累积成交量，价格上涨时加，下跌时减。
当OBV突破均线时产生信号，结合价格突破确认。
OBV用于识别资金流向。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (周期): [10, 15, 20, 25, 30]
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

    # 计算OBV
    df['obv'] = 0
    for i in range(1, len(df)):
        if df.iloc[i]['close'] > df.iloc[i-1]['close']:
            df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] + df.iloc[i]['volume']
        elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
            df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] - df.iloc[i]['volume']
        else:
            df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv']

    # 计算OBV均线
    df['obv_ma'] = df['obv'].rolling(window=period, min_periods=1).mean()

    # 计算价格突破
    df['price_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['price_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 做多信号: OBV上穿均线且价格突破新高
    condition1 = df['obv'] > df['obv_ma']
    condition2 = df['close'] > df['price_high'].shift(1)
    condition3 = df['obv'].shift(1) <= df['obv_ma'].shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 1

    # 做多平仓信号: OBV下穿均线
    condition1 = df['obv'] < df['obv_ma']
    condition2 = df['obv'].shift(1) >= df['obv_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: OBV下穿均线且价格突破新低
    condition1 = df['obv'] < df['obv_ma']
    condition2 = df['close'] < df['price_low'].shift(1)
    condition3 = df['obv'].shift(1) >= df['obv_ma'].shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1

    # 做空平仓信号: OBV上穿均线
    condition1 = df['obv'] > df['obv_ma']
    condition2 = df['obv'].shift(1) <= df['obv_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['obv', 'obv_ma', 'price_high', 'price_low', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    """
    periods = [10, 15, 20, 25, 30]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
