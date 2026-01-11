"""
动态布林带策略 (Dynamic Bollinger Bands)

原理:
根据ATR动态调整布林带宽度。
在高波动市场使用较宽的带宽，在低波动市场使用较窄的带宽。
这比固定带宽的布林带更能适应市场变化。

时间周期推荐:
- 4H: n=15-20
- 12H: n=20-30

参数范围:
- n (周期): [15, 20, 25, 30]
- std_dev (标准差倍数): [1.5, 2, 2.5]
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
    base_std_dev = para[1]

    # 计算ATR
    df['tr'] = df['high'] - df['low']
    df['tr'] = df['tr'].abs()
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    # 计算ATR的标准化因子
    df['atr_factor'] = df['atr'] / df['close'].rolling(window=period, min_periods=1).mean()

    # 动态调整标准差倍数
    df['dynamic_std'] = base_std_dev * (1 + df['atr_factor'] * 2)

    # 计算动态布林带
    df['bb_middle'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['bb_std'] = df['close'].rolling(window=period, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + df['dynamic_std'] * df['bb_std']
    df['bb_lower'] = df['bb_middle'] - df['dynamic_std'] * df['bb_std']

    # 做多信号: 价格突破上轨
    condition1 = df['close'] > df['bb_upper']
    condition2 = df['close'].shift(1) <= df['bb_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格回归中轨
    condition1 = df['close'] < df['bb_middle']
    condition2 = df['close'].shift(1) >= df['bb_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格突破下轨
    condition1 = df['close'] < df['bb_lower']
    condition2 = df['close'].shift(1) >= df['bb_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格回归中轨
    condition1 = df['close'] > df['bb_middle']
    condition2 = df['close'].shift(1) <= df['bb_middle'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tr', 'atr', 'atr_factor', 'dynamic_std', 'bb_middle', 'bb_std', 'bb_upper', 'bb_lower',
             'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 15, 20, 25, 30
    - 标准差倍数: 1.5, 2, 2.5
    """
    periods = [15, 20, 25, 30]
    std_devs = [1.5, 2, 2.5]

    para_list = []
    for period in periods:
        for std in std_devs:
            para_list.append([period, std])

    return para_list
