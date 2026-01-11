"""
正负波动策略 (Positive/Negative Divergence)

原理:
分别分析上涨日和下跌日，判断市场多空趋势。
+DI = 上涨日 / (上涨日 + 下跌日)
-DI = 下跌日 / (上涨日 + 下跌日)
DX = |+DI - -DI| / |+DI + -DI|

当+DI上穿-DI时做多，下穿时做空。
DX衡量趋势强度。

时间周期推荐:
- 4H: n=14
- 12H: n=14

参数范围:
- n (周期): [10, 14, 20]
"""

from cta_api.function import *

def signal(df, para=[14], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算价格变动
    df['price_change'] = df['close'] - df['close'].shift(1)
    df['tr'] = df['high'] - df['low']

    # 计算上涨日和下跌日
    df['up_day'] = df['price_change'].where(df['price_change'] > 0, df['tr'])
    df['down_day'] = df['price_change'].where(df['price_change'] < 0, -df['tr'])

    # 计算上涨日和下跌日EMA
    df['up_ema'] = df['up_day'].ewm(span=period, adjust=False).mean()
    df['down_ema'] = df['down_day'].ewm(span=period, adjust=False).mean()

    # 计算+DI和-DI
    df['plus_di'] = df['up_ema'] / (df['up_ema'] + df['down_ema']).abs()
    df['minus_di'] = df['up_ema'] / (df['up_ema'] + df['down_ema']).abs()

    # 计算DX
    df['dx'] = (df['plus_di'] - df['minus_di']).abs()

    # 做多信号: +DI上穿-DI
    condition1 = df['plus_di'] > df['minus_di']
    condition2 = df['plus_di'].shift(1) <= df['minus_di'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: +DI下穿-DI
    condition1 = df['plus_di'] < df['minus_di']
    condition2 = df['plus_di'].shift(1) >= df['minus_di'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: +DI下穿-DI
    condition1 = df['plus_di'] < df['minus_di']
    condition2 = df['plus_di'].shift(1) >= df['minus_di'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: +DI上穿-DI
    condition1 = df['plus_di'] > df['minus_di']
    condition2 = df['plus_di'].shift(1) <= df['minus_di'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['price_change', 'tr', 'up_day', 'down_day', 'up_ema', 'down_ema', 'plus_di', 'minus_di', 'dx', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 14, 20
    """
    periods = [10, 14, 20]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
