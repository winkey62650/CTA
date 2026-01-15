"""
Coppock Curve (估波曲线)

原理:
Coppock Curve 是一种长线动量指标，最初用于识别市场底部。
公式: WMA(10) of (ROC(14) + ROC(11))
本策略将其参数化，ROC周期随参数n缩放。

参数:
- n: ROC基准周期 (推荐 14)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    n = para[0]
    roc1_period = n
    roc2_period = int(n * 11 / 14) # 保持比例
    wma_period = int(n * 10 / 14)
    
    if roc2_period < 1: roc2_period = 1
    if wma_period < 2: wma_period = 2
    
    # ROC
    roc1 = df['close'].pct_change(roc1_period) * 100
    roc2 = df['close'].pct_change(roc2_period) * 100
    
    # WMA (Weighted Moving Average)
    # Pandas没有直接的WMA，用EWM近似或手动计算
    # 这里用EWM近似，span=wma_period
    # 或者手动实现WMA: weights = np.arange(1, w + 1)
    
    raw = roc1 + roc2
    
    # 使用 EWM 近似 WMA，平滑效果类似
    df['coppock'] = raw.ewm(span=wma_period).mean()
    
    # 信号: 穿越0轴
    # 实际上Coppock用于抄底，穿越0轴是确认右侧
    
    condition1 = df['coppock'] > 0
    condition2 = df['coppock'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_long'] = 1
    
    # 下穿0轴平仓/做空
    condition1 = df['coppock'] < 0
    condition2 = df['coppock'].shift(1) >= 0
    df.loc[condition1 & condition2, 'signal_long'] = 0
    df.loc[condition1 & condition2, 'signal_short'] = -1
    
    # 上穿0轴平空
    condition1 = df['coppock'] > 0
    condition2 = df['coppock'].shift(1) <= 0
    df.loc[condition1 & condition2, 'signal_short'] = 0
    
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['coppock', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20, 30, 50]
    return [[p] for p in periods]
