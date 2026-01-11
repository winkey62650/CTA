"""
TRIX指标策略 (TRIX)

原理:
TRIX是三重指数平滑移动平均的变化率。
它通过三次EMA平滑价格，再计算变化率来过滤短期波动。
TRIX上穿0时做多，下穿0时做空。

时间周期推荐:
- 1H: n=8-18
- 4H: n=12-24

参数范围:
- n (周期): [8, 12, 18, 24, 30]
"""

from cta_api.function import *

def signal(df, para=[15], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算第一层EMA
    df['ema1'] = df['close'].ewm(span=period, adjust=False).mean()

    # 计算第二层EMA
    df['ema2'] = df['ema1'].ewm(span=period, adjust=False).mean()

    # 计算第三层EMA
    df['ema3'] = df['ema2'].ewm(span=period, adjust=False).mean()

    # 计算TRIX (三重EMA的百分比变化率)
    df['trix'] = (df['ema3'] - df['ema3'].shift(1)) / df['ema3'].shift(1) * 100

    # 平滑TRIX
    df['trix'] = df['trix'].rolling(window=3, min_periods=1).mean()

    # 做多信号: TRIX > 0
    condition1 = df['trix'] > 0
    condition2 = df['trix'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: TRIX回落到0
    condition1 = df['trix'] < 0
    condition2 = df['trix'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: TRIX下穿0
    condition1 = df['trix'] < 0
    condition2 = df['trix'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: TRIX上穿0
    condition1 = df['trix'] > 0
    condition2 = df['trix'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ema1', 'ema2', 'ema3', 'trix', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 8, 12, 18, 24, 30
    """
    periods = [8, 12, 18, 24, 30]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
