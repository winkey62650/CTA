"""
自适应均线策略 (Kaufman's Adaptive Moving Average - KAMA)

原理:
KAMA根据市场的波动率自动调整平滑度。
在趋势市场中，KAMA快速响应价格变化；在震荡市场中，KAMA更加平滑，减少假信号。
效率比率(ER)用于衡量趋势强度，KAMA根据ER动态调整。

时间周期推荐:
- 4H: n=10-20
- 12H: n=15-30
- 24H: n=20-30

参数n范围: [5, 10, 15, 20, 25, 30]
"""

from cta_api.function import *

def signal(df, para=[20, 50], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [短期KAMA周期, 长期KAMA周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    short_period = para[0]
    long_period = para[1]

    # 计算KAMA
    df['kama_short'] = calculate_kama(df['close'], short_period)
    df['kama_long'] = calculate_kama(df['close'], long_period)

    # 做多信号: 短期KAMA上穿长期KAMA
    condition1 = df['kama_short'] > df['kama_long']
    condition2 = df['kama_short'].shift(1) <= df['kama_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 1

    # 做多平仓信号: 短期KAMA下穿长期KAMA
    condition1 = df['kama_short'] < df['kama_long']
    condition2 = df['kama_short'].shift(1) >= df['kama_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 短期KAMA下穿长期KAMA
    condition1 = df['kama_short'] < df['kama_long']
    condition2 = df['kama_short'].shift(1) >= df['kama_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = -1

    # 做空平仓信号: 短期KAMA上穿长期KAMA
    condition1 = df['kama_short'] > df['kama_long']
    condition2 = df['kama_short'].shift(1) <= df['kama_long'].shift(1)
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['kama_short', 'kama_long', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def calculate_kama(series, period):
    """
    计算自适应移动平均线
    1. 计算效率比率(ER): 方向性波动 / 总波动
    2. 计算平滑常数SC: (ER * (fastest - slowest) + slowest)^2
    3. KAMA = 前一日KAMA + SC * (当前价 - 前一日KAMA)
    """
    fastest = 2 / 3
    slowest = 2 / 31

    # 计算价格变化
    change = series.diff(period).abs()

    # 计算总波动
    volatility = series.diff().abs().rolling(window=period).sum()

    # 效率比率
    er = change / volatility
    er = er.fillna(0)

    # 平滑常数
    sc = (er * (fastest - slowest) + slowest) ** 2

    # 计算KAMA
    kama = series.copy()
    for i in range(period, len(series)):
        if i == period:
            kama.iloc[i] = series.iloc[:i+1].mean()
        else:
            kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (series.iloc[i] - kama.iloc[i-1])

    return kama


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 短期周期: 5, 10, 15, 20
    - 长期周期: 10, 15, 20, 25, 30
    - 短期 < 长期
    """
    short_periods = [5, 10, 15, 20]
    long_periods = [10, 15, 20, 25, 30]

    para_list = []
    for short in short_periods:
        for long in long_periods:
            if short < long:
                para_list.append([short, long])

    return para_list
