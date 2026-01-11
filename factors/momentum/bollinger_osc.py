"""
布林带震荡指标策略 (Bollinger Oscillator)

原理:
布林带震荡是布林带指标的震荡形式。
%B = (价格 - 下轨) / (上轨 - 下轨)
当%B < 0.2时超卖，> 0.8时超买。
价格回归中值时平仓。

时间周期推荐:
- 1H: n=10-15
- 4H: n=15-20

参数范围:
- n (周期): [10, 15, 20, 25]
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
    std_dev = para[1]

    # 计算布林带
    df['bb_middle'] = df['close'].rolling(window=period, min_periods=1).mean()
    df['bb_std'] = df['close'].rolling(window=period, min_periods=1).std()
    df['bb_upper'] = df['bb_middle'] + std_dev * df['bb_std']
    df['bb_lower'] = df['bb_middle'] - std_dev * df['bb_std']

    # 计算%B震荡指标
    df['pct_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # 做多信号: %B < 0.2 (超卖反弹)
    condition1 = df['pct_b'] < 0.2
    condition2 = df['pct_b'].shift(1) >= 0.2
    condition3 = df['pct_b'] < df['pct_b'].shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 1

    # 做多平仓信号: %B回归到0.5
    condition1 = df['pct_b'] >= 0.5
    condition2 = df['pct_b'].shift(1) < 0.5
    df.loc[(condition1 | condition2) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: %B > 0.8 (超买回调)
    condition1 = df['pct_b'] > 0.8
    condition2 = df['pct_b'].shift(1) <= 0.8
    condition3 = df['pct_b'] > df['pct_b'].shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1

    # 做空平仓信号: %B回归到0.5
    condition1 = df['pct_b'] <= 0.5
    condition2 = df['pct_b'].shift(1) > 0.5
    df.loc[(condition1 | condition2) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['bb_middle', 'bb_std', 'bb_upper', 'bb_lower', 'pct_b', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25
    - 标准差倍数: 1.5, 2, 2.5
    """
    periods = [10, 15, 20, 25]
    std_devs = [1.5, 2, 2.5]

    para_list = []
    for period in periods:
        for std in std_devs:
            para_list.append([period, std])

    return para_list
