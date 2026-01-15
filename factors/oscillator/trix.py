"""
TRIX随机指标策略

原理:
TRIX由两条线组成，衡量趋势强度。
TRIX上穿零轴且>0时做多，下穿零轴且<0时做空。
经典震荡指标，适用于判断趋势反转。

时间周期推荐:
- 1H: n=10-20
- 4H: n=14-28
- 12H: n=14-30
- 24H: n=14-40

参数n范围: [10, 14, 21, 28]
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[14, 40], proportion=1, leverage_rate=1):
    period = int(para[0])
    signal_period = int(para[1]) # Matrix length or signal line length? usually TRIX and Matrix

    # TRIX Calculation
    # 1. EMA1 of Close
    ema1 = df['close'].ewm(span=period, adjust=False).mean()
    # 2. EMA2 of EMA1
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    # 3. EMA3 of EMA2
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    
    # 4. TRIX = (EMA3 - EMA3_prev) / EMA3_prev * 100
    df['trix'] = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
    
    # 5. MATRIX (Signal Line) = MA(TRIX)
    df['matrix'] = df['trix'].rolling(window=signal_period, min_periods=1).mean()

    # Signals
    # Buy: TRIX crosses above MATRIX (Golden Cross) or TRIX crosses above 0?
    # Docstring says: TRIX上穿零轴且>0? 
    # Standard TRIX strategy: Golden Cross (TRIX > MATRIX) or Zero Cross.
    # Let's follow docstring hint "TRIX上穿零轴" -> Crosses 0.
    
    # Strategy A: Zero Cross
    # buy_signal = (df['trix'] > 0) & (df['trix'].shift(1) <= 0)
    # sell_signal = (df['trix'] < 0) & (df['trix'].shift(1) >= 0)
    
    # Strategy B: Signal Line Cross (TRIX vs MATRIX)
    buy_signal = (df['trix'] > df['matrix']) & (df['trix'].shift(1) <= df['matrix'].shift(1))
    sell_signal = (df['trix'] < df['matrix']) & (df['trix'].shift(1) >= df['matrix'].shift(1))
    
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[sell_signal, 'signal_short'] = -1
    
    # Close signals (optional, or just reverse)
    # If using cross strategy, we are always in market or wait for reverse?
    # Let's assume always in market for simplicity or add exit logic.
    # Close Long if TRIX < MATRIX
    df.loc[df['trix'] < df['matrix'], 'signal_long'] = 0
    df.loc[df['trix'] > df['matrix'], 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['trix', 'matrix', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 21, 28]
    signal_periods = [9, 12, 20] # Standard signal lengths
    
    para_list = []
    for p in periods:
        for s in signal_periods:
            para_list.append([p, s])
    return para_list
