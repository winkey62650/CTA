"""
RSI指标策略 (Relative Strength Index)

原理:
RSI衡量价格变动的强度和速度。
RSI = 100 - (100 / (1 + RS))
RS = 平均上涨日 / (平均上涨日 + 平均下跌日)
RSI在70以上超买，30以下超卖。
RSI上穿30时做多(超卖反弹)，下穿70时做空(超买回调)。

时间周期推荐:
- 1H: n=5-14
- 4H: n=14

参数范围:
- n (周期): [5, 7, 14, 21]
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

    # 计算价格变化
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 计算RS
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / (avg_gain + avg_loss)

    # 计算RSI
    df['rsi'] = 100 - (100 / (1 + rs))

    # 做多信号: RSI上穿30 (超卖反弹)
    condition1 = df['rsi'] > 30
    condition2 = df['rsi'].shift(1) <= 30
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: RSI回落到50
    condition1 = df['rsi'] < 50
    condition2 = df['rsi'].shift(1) >= 50
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: RSI下穿70 (超买回调)
    condition1 = df['rsi'] < 70
    condition2 = df['rsi'].shift(1) >= 70
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: RSI回升到50
    condition1 = df['rsi'] > 50
    condition2 = df['rsi'].shift(1) <= 50
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['rsi', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 7, 14, 21
    """
    periods = [5, 7, 14, 21]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
