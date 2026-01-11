"""
资金流量指数策略 (Money Flow Index - MFI)

原理:
MFI结合价格和成交量来衡量资金流入流出。
MFI = 100 - (100 / (1 + 资金流比率))
资金流比率 = 正向MFP / 负向MFP
MFI > 80超买，< 20超卖。
价格结合MFI方向产生信号。

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

    # 计算典型价格
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3

    # 计算资金流
    df['raw_mf'] = df['tp'] * df['volume']
    df['mf_up'] = df['raw_mf'].where(df['tp'] > df['tp'].shift(1), 0)
    df['mf_down'] = df['raw_mf'].where(df['tp'] < df['tp'].shift(1), 0).abs()

    # 计算MFI
    df['mfi'] = 100 - (100 / (1 + df['mf_up'].rolling(window=period).sum() /
                                        (df['mf_down'].rolling(window=period).sum() + 0.0001)))

    # 做多信号: MFI < 20 (超卖且价格上穿均线)
    condition1 = df['mfi'] < 20
    condition2 = df['close'] > df['close'].rolling(window=period).mean()
    condition3 = df['close'].shift(1) <= df['close'].rolling(window=period).mean().shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 1

    # 做多平仓信号: MFI > 80 (超买)
    condition1 = df['mfi'] > 80
    df.loc[condition1 & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: MFI > 80 (超买且价格下穿均线)
    condition1 = df['mfi'] > 80
    condition2 = df['close'] < df['close'].rolling(window=period).mean()
    condition3 = df['close'].shift(1) >= df['close'].rolling(window=period).mean().shift(1)
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1

    # 做空平仓信号: MFI < 20 (超卖)
    condition1 = df['mfi'] < 20
    df.loc[condition1 & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tp', 'raw_mf', 'mf_up', 'mf_down', 'mfi', 'signal_long', 'signal_short'], axis=1, inplace=True)

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
