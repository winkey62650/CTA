"""
相对强弱指标策略 (RSI)

原理:
RSI衡量价格变动的速度和变化，范围0-100。
RSI < 30为超卖区(买入信号)，RSI > 70为超买区(卖出信号)。
适用于震荡行情中的超买超卖交易。

时间周期推荐:
- 1H: n=7-14
- 4H: n=14-21
- 12H: n=14-28
- 24H: n=14-30

参数n范围: [7, 10, 14, 21, 28, 30]
"""

from cta_api.function import *

def signal(df, para=[14, 30, 70], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [RSI周期, 超卖阈值, 超买阈值]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    oversold = para[1]
    overbought = para[2]

    # 计算RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()

    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 买入信号: RSI上穿超卖线
    prev_rsi = df['rsi'].shift(1)
    buy_signal = (df['rsi'] > oversold) & (prev_rsi <= oversold)
    df.loc[buy_signal, 'signal_long'] = 1

    # 做多平仓: RSI回到50或触及超买线
    df.loc[(df['rsi'] >= 50) | (df['rsi'] >= overbought), 'signal_long'] = 0

    # 卖出信号: RSI下穿超买线
    sell_signal = (df['rsi'] < overbought) & (prev_rsi >= overbought)
    df.loc[sell_signal, 'signal_short'] = -1

    # 做空平仓: RSI回到50或触及超卖线
    df.loc[(df['rsi'] <= 50) | (df['rsi'] <= oversold), 'signal_short'] = 0

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

    RSI周期: 7, 14, 21, 28
    超卖线: 20, 25, 30, 35
    超买线: 65, 70, 75, 80
    """
    periods = [7, 14, 21, 28]
    oversold_levels = [20, 25, 30, 35]
    overbought_levels = [65, 70, 75, 80]

    para_list = []
    for period in periods:
        for os in oversold_levels:
            for ob in overbought_levels:
                if os < ob:
                    para_list.append([period, os, ob])

    return para_list
