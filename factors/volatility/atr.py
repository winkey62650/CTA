"""
ATR平均真实波幅策略

原理:
ATR衡量市场波动率，用于设置动态止损和仓位管理。
不直接生成交易信号，用于辅助其他策略的风险控制。

时间周期推荐:
- 1H: n=7-14
- 4H: n=14-20
- 12H: n=20-30
- 24H: n=20-50

参数n范围: [7, 14, 21, 30]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[14, 1.5], proportion=1, leverage_rate=1):
    period = para[0]
    multiplier = para[1]

    high_low = df['high'] - df['low'].shift(1)
    high_close = np.abs(df['high'] - df['close'].shift(1))
    close_low = np.abs(df['close'] - df['low'].shift(1))

    df['tr'] = np.maximum.reduce([high_low, high_close, close_low], axis=1)
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    df['upper_band'] = df['close'] + multiplier * df['atr']
    df['lower_band'] = df['close'] - multiplier * df['atr']

    df.drop(['tr', 'atr', 'upper_band', 'lower_band'], axis=1, inplace=True)

    return df

def para_list():
    periods = [7, 14, 21, 30]
    multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])
    return para_list
