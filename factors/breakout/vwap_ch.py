"""
VWAP突破策略 (Volume Weighted Average Price)

原理:
成交量加权平均价反映价格的真实重心。
VWAP = Σ(价格 × 成交量) / Σ成交量
当价格突破VWAP时产生信号，结合成交量确认。
VWAP突破可以识别价格偏离合理区间的机会。

时间周期推荐:
- 4H: n=20-40
- 12H: n=30-60

参数范围:
- n (周期): [20, 30, 40, 50, 60]
"""

from cta_api.function import *

def signal(df, para=[30], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算VWAP
    df['vwap'] = (df['close'] * df['volume']).rolling(window=period, min_periods=1).sum() / df['volume'].rolling(window=period, min_periods=1).sum()

    # 计算价格突破
    df['price_high'] = df['high'].rolling(window=period, min_periods=1).max()
    df['price_low'] = df['low'].rolling(window=period, min_periods=1).min()

    # 计算成交量均线
    df['vol_ma'] = df['volume'].rolling(window=period, min_periods=1).mean()

    # 计算成交量放大
    df['vol_surge'] = df['volume'] > df['vol_ma'] * 1.5

    # 做多信号: 价格突破VWAP且成交量放大
    condition1 = df['close'] > df['vwap'].shift(1)
    condition2 = df['vol_surge']
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回落VWAP或成交量萎缩
    condition1 = df['close'] < df['vwap']
    condition2 = df['vol_surge'].shift(1) & ~df['vol_surge']
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: 价格跌破VWAP且成交量放大
    condition1 = df['close'] < df['vwap'].shift(1)
    condition2 = df['vol_surge']
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回升VWAP或成交量萎缩
    condition1 = df['close'] > df['vwap']
    condition2 = df['vol_surge'].shift(1) & ~df['vol_surge']
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['vwap', 'price_high', 'price_low', 'vol_ma', 'vol_surge', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 20, 30, 40, 50, 60
    """
    periods = [20, 30, 40, 50, 60]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
