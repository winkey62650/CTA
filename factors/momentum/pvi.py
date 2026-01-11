"""
正量指标策略 (Positive Volume Index - PVI)

原理:
PVI仅在价格上涨时累积成交量，下跌时成交量保持不变。
PVI = 前一日PVI + (价格上涨时) * 成交量变化率
PVI上涨表示强势市场，下跌表示弱势。
PVI上穿均线时做多，下穿时做空。

时间周期推荐:
- 4H: n=50-100
- 12H: n=100-200

参数范围:
- n (周期): [50, 100, 150, 200]
"""

from cta_api.function import *

def signal(df, para=[100], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算价格变化
    df['price_change'] = df['close'] - df['close'].shift(1)

    # 计算PVI
    df['volume_change'] = df['volume'].pct_change()
    df['pvi'] = df['volume'].shift(1) * 0 + df['volume']

    for i in range(1, len(df)):
        if df.iloc[i]['price_change'] > 0:
            df.iloc[i, df.columns.get_loc('pvi')] = df.iloc[i-1]['pvi'] + df.iloc[i]['volume_change']
        else:
            df.iloc[i, df.columns.get_loc('pvi')] = df.iloc[i-1]['pvi']

    # 计算PVI均线
    df['pvi_ma'] = df['pvi'].rolling(window=period, min_periods=1).mean()

    # 做多信号: PVI上穿均线
    condition1 = df['pvi'] > df['pvi_ma']
    condition2 = df['pvi'].shift(1) <= df['pvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: PVI下穿均线
    condition1 = df['pvi'] < df['pvi_ma']
    condition2 = df['pvi'].shift(1) >= df['pvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: PVI下穿均线
    condition1 = df['pvi'] < df['pvi_ma']
    condition2 = df['pvi'].shift(1) >= df['pvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: PVI上穿均线
    condition1 = df['pvi'] > df['pvi_ma']
    condition2 = df['pvi'].shift(1) <= df['pvi_ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['price_change', 'volume_change', 'pvi', 'pvi_ma', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 50, 100, 150, 200
    """
    periods = [50, 100, 150, 200]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
