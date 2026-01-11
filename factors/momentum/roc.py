"""
ROC指标策略 (Rate of Change)

原理:
计算价格的变化率百分比。
ROC = (当前价 - N周期前价格) / N周期前价格 * 100
正值表示上涨，负值表示下跌。
ROC上穿0时做多，下穿0时做空。

时间周期推荐:
- 1H: n=5-15
- 4H: n=10-20

参数范围:
- n (周期): [5, 10, 15, 20, 25]
"""

from cta_api.function import *

def signal(df, para=[12], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算ROC
    df['roc'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100

    # 做多信号: ROC > 0 (上涨动能)
    condition1 = df['roc'] > 0
    condition2 = df['roc'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: ROC回落到0
    condition1 = df['roc'] < 0
    condition2 = df['roc'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: ROC下穿0 (下跌动能)
    condition1 = df['roc'] < 0
    condition2 = df['roc'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: ROC上穿0 (反转动能)
    condition1 = df['roc'] > 0
    condition2 = df['roc'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['roc', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 5, 10, 15, 20, 25
    """
    periods = [5, 10, 15, 20, 25]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
