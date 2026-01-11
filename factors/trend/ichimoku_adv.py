"""
一目均衡表策略 (Advanced Ichimoku)

原理:
Ichimoku云图是综合技术分析系统，包含:
- 转换线(Tenkan-sen): 9日最高最低均价
- 基准线(Kijun-sen): 26日最高最低均价
- 先行带A(Senkou Span A): 转换线与基准线中值前移26日
- 先行带B(Senkou Span B): 52日最高最低均价前移26日
- 迟行线(Chikou Span): 当日收盘价后移26日

时间周期推荐:
- 4H: params=(9,26,52)
- 12H: params=(9,26,52)
- 24H: params=(9,26,52)

参数范围:
- tenkan: 5-15 (推荐9)
- kijun: 15-35 (推荐26)
- senkou: 40-60 (推荐52)
"""

from cta_api.function import *

def signal(df, para=[9, 26, 52], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [转换线周期, 基准线周期, 后行线周期]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    tenkan_period = para[0]
    kijun_period = para[1]
    senkou_period = para[2]

    # 计算转换线
    df['tenkan_sen'] = (df['high'].rolling(window=tenkan_period).max() +
                        df['low'].rolling(window=tenkan_period).min()) / 2

    # 计算基准线
    df['kijun_sen'] = (df['high'].rolling(window=kijun_period).max() +
                        df['low'].rolling(window=kijun_period).min()) / 2

    # 计算先行带
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    df['senkou_span_b'] = ((df['high'].rolling(window=senkou_period).max() +
                         df['low'].rolling(window=senkou_period).min()) / 2).shift(26)

    # 计算迟行线
    df['chikou_span'] = df['close'].shift(-26)

    # 云图上下沿
    df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
    df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)

    # 做多信号: 转换线上穿基准线，且价格在云上
    condition1 = df['tenkan_sen'] > df['kijun_sen']
    condition2 = df['tenkan_sen'].shift(1) <= df['kijun_sen'].shift(1)
    condition3 = df['close'] > df['cloud_bottom']
    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 1

    # 做多平仓信号: 转换线下穿基准线或价格跌破云底
    condition1 = df['tenkan_sen'] < df['kijun_sen']
    condition2 = df['tenkan_sen'].shift(1) >= df['kijun_sen'].shift(1)
    condition3 = df['close'] < df['cloud_bottom']
    df.loc[(condition1 & condition2) | condition3, 'signal_long'] = 0

    # 做空信号: 转换线下穿基准线，且价格在云下
    condition1 = df['tenkan_sen'] < df['kijun_sen']
    condition2 = df['tenkan_sen'].shift(1) >= df['kijun_sen'].shift(1)
    condition3 = df['close'] < df['cloud_top']
    df.loc[condition1 & condition2 & condition3, 'signal_short'] = -1

    # 做空平仓信号: 转换线上穿基准线或价格升破云顶
    condition1 = df['tenkan_sen'] > df['kijun_sen']
    condition2 = df['tenkan_sen'].shift(1) <= df['kijun_sen'].shift(1)
    condition3 = df['close'] > df['cloud_top']
    df.loc[(condition1 & condition2) | condition3, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['tenkan_sen', 'kijun_sen', 'senkou_span_a', 'senkou_span_b',
             'chikou_span', 'cloud_top', 'cloud_bottom', 'signal_long', 'signal_short'],
            axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 转换线: 5, 7, 9, 12, 15
    - 基准线: 15, 20, 26, 30, 35
    - 后行线: 40, 45, 52, 60
    - 转换线 < 基准线 < 后行线
    """
    tenkan_periods = [5, 7, 9, 12, 15]
    kijun_periods = [15, 20, 26, 30, 35]
    senkou_periods = [40, 45, 52, 60]

    para_list = []
    for tenkan in tenkan_periods:
        for kijun in kijun_periods:
            for senkou in senkou_periods:
                if tenkan < kijun and kijun < senkou:
                    para_list.append([tenkan, kijun, senkou])

    return para_list
