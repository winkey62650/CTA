"""
资金流量指数策略 (Money Flow Index - MFI)

原理:
MFI结合价格和成交量，衡量买卖压力。
TP = (最高价 + 最低价 + 收盘价) / 3
MF = TP × 成交量 / (TP × N周期均价)
MFI = 100 - (100 / (1 + MF))
MFI > 80超买，< 20超卖。
MFI方向判断资金流入流出。

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

    # 计算TP
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3

    # 计算价格均价
    df['typical_price'] = df['tp'].rolling(window=period, min_periods=1).mean()

    # 计算正负资金流
    df['pos_mf'] = df['tp'] * df['volume']
    df['neg_mf'] = -df['tp'] * df['volume']

    # 分别累积
    df['pos_mf_sum'] = df['pos_mf'].rolling(window=period, min_periods=1).sum()
    df['neg_mf_sum'] = df['neg_mf'].rolling(window=period, min_periods=1).sum()

    # 计算MFI
    df['mfi'] = 100 - (100 / (1 + (df['pos_mf'] / df['neg_mf_sum']))

    # 做多信号: MFI从超卖上穿20 (资金流入增加)
    condition1 = df['mfi'] > 20
    condition2 = df['mfi'].shift(1) <= 20
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: MFI回落到80
    condition1 = df['mfi'] < 80
    df.loc[(condition1) & df['signal_long'].shift(1).notnull(), 'signal_long'] = 0

    # 做空信号: MFI从超买下穿20 (资金流出增加)
    condition1 = df['mfi'] < 20
    condition2 = df['mfi'].shift(1) >= 20
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: MFI回升到80
    condition1 = df['mfi'] > 80
    df.loc[(condition1) & df['signal_short'].shift(1).notnull(), 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tp', 'typical_price', 'pos_mf', 'neg_mf', 'pos_mf_sum', 'neg_mf_sum', 'mfi', 'signal_long', 'signal_short'], axis=1, inplace=True)

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
