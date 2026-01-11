"""
布林带%B策略 (Bollinger Band %B)

原理:
%B指标标准化布林带位置，计算公式: (价格 - 下轨) / (上轨 - 下轨)。
%B > 0.8时超买(可能回调)，%B < 0.2时超卖(可能反弹)。
结合趋势方向产生信号。

时间周期推荐:
- 1H: n=10-15
- 4H: n=15-20

参数范围:
- n (周期): [10, 15, 20, 25, 30]
- std_dev (标准差倍数): [2, 2.5]
"""

from cta_api.function import *

def signal(df, para=[20, 2], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 标准差倍数]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    std_dev = para[1]

    # 计算布林带
    df['bb_middle'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['bb_std'] = df['close'].rolling(window=period, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + std_dev * df['bb_std']
    df['bb_lower'] = df['bb_middle'] - std_dev * df['bb_std']

    # 计算%B指标
    df['bb_pctb'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # 计算趋势方向(价格与中轨关系)
    df['trend'] = df['close'] - df['bb_middle']

    # 做多信号: %B超卖且价格上升
    condition1 = df['bb_pctb'] < 0.2
    condition2 = df['close'] > df['bb_middle']
    condition3 = df['trend'] > df['trend'].shift(1)
    condition4 = df['close'].shift(1) <= df['bb_middle'].shift(1)
    df.loc[condition1 & condition2 & condition3 & condition4, 'signal_long'] = 1

    # 做多平仓信号: %B回归中性或价格跌破中轨
    condition1 = df['bb_pctb'] > 0.8
    condition2 = df['close'] < df['bb_middle']
    condition3 = df['close'].shift(1) >= df['bb_middle'].shift(1)
    df.loc[(condition1 | condition2 | condition3) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: %B超买且价格下降
    condition1 = df['bb_pctb'] > 0.8
    condition2 = df['close'] < df['bb_middle']
    condition3 = df['trend'] < df['trend'].shift(1)
    condition4 = df['close'].shift(1) >= df['bb_middle'].shift(1)
    df.loc[condition1 & condition2 & condition3 & condition4, 'signal_short'] = -1

    # 做空平仓信号: %B回归中性或价格升破中轨
    condition1 = df['bb_pctb'] < 0.2
    condition2 = df['close'] > df['bb_middle']
    condition3 = df['close'].shift(1) <= df['bb_middle'].shift(1)
    df.loc[(condition1 | condition2 | condition3) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['bb_middle', 'bb_std', 'bb_upper', 'bb_lower', 'bb_pctb', 'trend',
             'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    - 标准差倍数: 2, 2.5
    """
    periods = [10, 15, 20, 25, 30]
    std_devs = [2, 2.5]

    para_list = []
    for period in periods:
        for std in std_devs:
            para_list.append([period, std])

    return para_list
