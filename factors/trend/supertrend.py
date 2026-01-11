"""
Supertrend超级趋势策略

原理:
Supertrend基于ATR和波动率计算动态止损线。
价格位于Supertrend线上方做多，位于下方做空。
经典趋势跟踪策略，减少回撤。

时间周期推荐:
- 1H: n=10, mult=3.0
- 4H: n=10, mult=2.5
- 12H: n=10, mult=2.0
- 24H: n=10, mult=1.5

参数n范围: [(10, 3.0), (10, 2.5), (10, 2.0)]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[10, 3.0], proportion=1, leverage_rate=1):
    period = para[0]
    multiplier = para[1]

    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'])
    close_low = np.abs(df['close'] - df['low'])

    df['tr'] = np.maximum.reduce([high_low, high_close, close_low], axis=1)
    df['atr'] = df['tr'].rolling(window=period, min_periods=1).mean()

    df['basic_upper'] = df['close'] + multiplier * df['atr']
    df['final_upper'] = df['basic_upper'].copy()

    for i in range(1, len(df)):
        df.loc[i, 'final_upper'] = df.loc[i, 'basic_upper']
        if df.loc[i, 'high'] > df.loc[i, 'final_upper']:
            df.loc[i, 'final_upper'] = df.loc[i, 'high']
            df.loc[i, 'supertrend'] = df.loc[i, 'final_upper'] - multiplier * df.loc[i, 'atr']

    df['trend'] = np.where(df['close'] > df['supertrend'], 1, -1)

    buy_signal = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df.loc[buy_signal, 'signal_long'] = 1

    sell_signal = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    df.loc[sell_signal, 'signal_short'] = -1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['tr', 'atr', 'basic_upper', 'final_upper', 'supertrend', 'trend', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10]
    multipliers = [3.0, 2.5, 2.0]

    para_list = []
    for mult in multipliers:
        para_list.append([period, mult])
    return para_list
