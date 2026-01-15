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
import pandas as pd

def signal(df, para=[10, 3.0], proportion=1, leverage_rate=1):
    period = int(para[0])
    multiplier = float(para[1])

    # Calculate ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift(1))
    close_low = np.abs(df['close'] - df['low'].shift(1))
    
    tr = np.maximum.reduce([high_low, high_close, close_low])
    # ATR smoothing (Wilder's smoothing is standard for Supertrend usually, but SMA is also used)
    # Using simple rolling mean as in original code
    atr = pd.Series(tr).rolling(window=period, min_periods=1).mean()

    # Basic bands
    hl2 = (df['high'] + df['low']) / 2
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)

    # Final bands initialization
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    supertrend = pd.Series(index=df.index, dtype='float64')
    
    # Iterative calculation for Final Bands and Supertrend
    # Using numpy arrays for speed
    close_arr = df['close'].values
    bu_arr = basic_upper.values
    bl_arr = basic_lower.values
    fu_arr = np.zeros(len(df))
    fl_arr = np.zeros(len(df))
    st_arr = np.zeros(len(df))
    trend_arr = np.zeros(len(df)) # 1 for up, -1 for down

    # Initialize first values
    fu_arr[0] = bu_arr[0]
    fl_arr[0] = bl_arr[0]
    
    for i in range(1, len(df)):
        # Final Upper Band
        if (bu_arr[i] < fu_arr[i-1]) or (close_arr[i-1] > fu_arr[i-1]):
            fu_arr[i] = bu_arr[i]
        else:
            fu_arr[i] = fu_arr[i-1]
            
        # Final Lower Band
        if (bl_arr[i] > fl_arr[i-1]) or (close_arr[i-1] < fl_arr[i-1]):
            fl_arr[i] = bl_arr[i]
        else:
            fl_arr[i] = fl_arr[i-1]
            
        # Supertrend
        if i == 0:
            trend_arr[i] = 1
        else:
            # Determine trend
            if trend_arr[i-1] == 1:
                if close_arr[i] < fl_arr[i]:
                    trend_arr[i] = -1
                else:
                    trend_arr[i] = 1
            else:
                if close_arr[i] > fu_arr[i]:
                    trend_arr[i] = 1
                else:
                    trend_arr[i] = -1
        
        if trend_arr[i] == 1:
            st_arr[i] = fl_arr[i]
        else:
            st_arr[i] = fu_arr[i]

    df['supertrend'] = st_arr
    df['trend'] = trend_arr

    # Generate signals
    buy_signal = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df.loc[buy_signal, 'signal_long'] = 1

    sell_signal = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    df.loc[sell_signal, 'signal_short'] = -1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['supertrend', 'trend', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10]
    multipliers = [3.0, 2.5, 2.0]

    para_list = []
    for period in periods:
        for mult in multipliers:
            para_list.append([period, mult])
    return para_list
