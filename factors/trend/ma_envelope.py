"""
移动平均包络策略 (MA Envelope)

原理:
在均线上下加上固定百分比的包络线，形成交易通道。
价格触及上包络线时视为超买，可能回调；触及下包络线时视为超卖，可能反弹。
但在强趋势中，包络线突破可以作为延续信号。

时间周期推荐:
- 4H: n=10-30, pct=2-5
- 12H: n=20-50, pct=2-5

参数范围:
- n (均线周期): [10, 15, 20, 30, 40, 50]
- pct (包络百分比): [0.02, 0.03, 0.04, 0.05]
"""

from cta_api.function import *

def signal(df, para=[20, 0.03], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [均线周期, 包络百分比]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    ma_period = para[0]
    envelope_pct = para[1]

    # 计算均线
    df['ma'] = df['close'].rolling(window=ma_period, min_periods=1).mean()

    # 计算包络线
    df['envelope_upper'] = df['ma'] * (1 + envelope_pct)
    df['envelope_lower'] = df['ma'] * (1 - envelope_pct)

    # 做多信号: 价格突破上包络线（趋势延续）或从下包络线反弹（均值回归）
    # 策略A: 突破上包络线（趋势延续）
    condition1 = df['close'] > df['envelope_upper']
    condition2 = df['close'].shift(1) <= df['envelope_upper'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 价格跌破均线
    condition1 = df['close'] < df['ma']
    condition2 = df['close'].shift(1) >= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格跌破下包络线（趋势延续）
    condition1 = df['close'] < df['envelope_lower']
    condition2 = df['close'].shift(1) >= df['envelope_lower'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 价格升破均线
    condition1 = df['close'] > df['ma']
    condition2 = df['close'].shift(1) <= df['ma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['ma', 'envelope_upper', 'envelope_lower', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 均线周期: 10, 15, 20, 30, 40, 50
    - 包络百分比: 2%, 3%, 4%, 5%
    """
    ma_periods = [10, 15, 20, 30, 40, 50]
    envelope_pcts = [0.02, 0.03, 0.04, 0.05]

    para_list = []
    for ma in ma_periods:
        for pct in envelope_pcts:
            para_list.append([ma, pct])

    return para_list
