"""
动向指数策略 (Directional Movement Index - DX)

原理:
DX是+DI和-DI的标准化指标，用于衡量趋势强度。
DX = |+DI - -DI| / |+DI + -DI| × 100
DX值在0-100之间，数值越大趋势越强。
当DX > 25时为强趋势，< 20时为弱趋势。

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

    # 做多信号: DX > 25 (强趋势且价格上涨)
    condition1 = df['dx'] > 25
    condition2 = df['close'] > df['close'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: DX回落到20
    condition1 = df['dx'] < 20
    df.loc[(condition1) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: DX < 25 (弱趋势且价格下跌)
    condition1 = df['dx'] < 20
    condition2 = df['close'] < df['close'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: DX回升到25
    condition1 = df['dx'] > 20
    df.loc[(condition1) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

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
