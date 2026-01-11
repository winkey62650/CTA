"""
RSI背离策略 (RSI Divergence)

原理:
比较价格与RSI的走势，当出现背离时产生信号。
顶背离: 价格创新高，RSI不创新高（看跌信号）
底背离: 价格创新低，RSI不创新低（看涨信号）
背离通常预示趋势反转。

时间周期推荐:
- 4H: n=14
- 12H: n=14

参数范围:
- rsi_period: [7, 14, 21]
- divergence_period: [5, 10, 15, 20]
"""

from cta_api.function import *

def signal(df, para=[14, 10], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [RSI周期, 背离确认周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    rsi_period = para[0]
    divergence_period = para[1]

    # 计算RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
    avg_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 计算价格高点
    df['price_high'] = df['high'].rolling(window=divergence_period, min_periods=1).max()
    df['rsi_high'] = df['rsi'].rolling(window=divergence_period, min_periods=1).max()

    # 计算RSI顶背离: 价格创新高，RSI未创新高
    condition1 = df['close'] == df['price_high']
    condition2 = df['rsi'] < df['rsi_high']
    condition3 = df['rsi'] > 50  # RSI在高位区域
    condition4 = df['close'].shift(1) < df['price_high'].shift(1)
    condition5 = df['rsi'].shift(1) < df['rsi_high'].shift(1)
    df.loc[condition1 & condition2 & condition3 & condition4 & condition5, 'signal_long'] = 0  # 顶背离平多仓

    # 计算RSI底背离: 价格创新低，RSI未创新低
    df['price_low'] = df['low'].rolling(window=divergence_period, min_periods=1).min()
    df['rsi_low'] = df['rsi'].rolling(window=divergence_period, min_periods=1).min()

    condition1 = df['close'] == df['price_low']
    condition2 = df['rsi'] > df['rsi_low']
    condition3 = df['rsi'] < 50  # RSI在低位区域
    condition4 = df['close'].shift(1) > df['price_low'].shift(1)
    condition5 = df['rsi'].shift(1) > df['rsi_low'].shift(1)
    df.loc[condition1 & condition2 & condition3 & condition4 & condition5, 'signal_long'] = 1  # 底背离做多

    # 平仓信号: 背离消失
    df['signal_long'] = df['signal_long'].ffill()
    df.loc[df['signal_long'].shift(1) == 1, 'signal_long'] = 0

    # 合并信号
    df['signal'] = df['signal_long'].replace(0, -1)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['delta', 'gain', 'loss', 'avg_gain', 'avg_loss', 'rs', 'rsi_high', 'rsi_low',
             'price_high', 'price_low'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - RSI周期: 7, 14, 21
    - 背离确认周期: 5, 10, 15, 20
    """
    rsi_periods = [7, 14, 21]
    divergence_periods = [5, 10, 15, 20]

    para_list = []
    for rsi in rsi_periods:
        for div in divergence_periods:
            para_list.append([rsi, div])

    return para_list
