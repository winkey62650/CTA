"""
Chaikin振荡器策略 (Chaikin Oscillator)

原理:
基于成交量的震荡指标。
当价格上涨时成交量增加，下跌时成交量减少。
C = 成交量EMA - 负成交量EMA
CMA = 成交量平滑 / 下跌成交量平滑
当C > CMA时做多，C < CMA时做空。
成交量用于确认价格变动方向。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30

参数范围:
- n (周期): [10, 15, 20, 25, 30]
"""

from cta_api.function import *

def signal(df, para=[20], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]

    # 计算价格变动方向
    df['price_change'] = df['close'] - df['open']

    # 计算成交量加权
    df['clv'] = df['price_change'] * df['volume']
    df['clv'] = np.where(df['clv'] > 0, df['clv'], 0)

    # 计算EMA成交量
    df['ema_vol_up'] = df['clv'].ewm(span=period, adjust=False).mean()
    df['ema_vol_down'] = -df['clv'].ewm(span=period, adjust=False).mean()
    df['cma'] = (df['ema_vol_up'] + df['ema_vol_down']).abs()

    # 做多信号: C > CMA (上涨资金流入)
    condition1 = df['ema_vol_up'] > df['cma']
    condition2 = df['ema_vol_up'].shift(1) <= df['cma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: C < CMA (转为下跌资金流出)
    condition1 = df['ema_vol_up'] < df['cma']
    condition2 = df['ema_vol_up'].shift(1) >= df['cma'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: C < CMA (下跌资金流出)
    condition1 = df['ema_vol_up'] < df['cma']
    condition2 = df['ema_vol_up'].shift(1) >= df['cma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: C > CMA (转为上涨资金流入)
    condition1 = df['ema_vol_up'] > df['cma']
    condition2 = df['ema_vol_up'].shift(1) <= df['cma'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['price_change', 'clv', 'ema_vol_up', 'ema_vol_down', 'cma', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30
    """
    periods = [10, 15, 20, 25, 30]

    para_list = []
    for period in periods:
        para_list.append([period])

    return para_list
