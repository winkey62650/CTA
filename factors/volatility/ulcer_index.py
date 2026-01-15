"""
Ulcer Index (溃疡指数)

原理:
Ulcer Index 衡量价格下行的深度和持续时间（即回撤风险）。
与标准差不同，它只关注下行波动。
UI值越低，表示上升趋势越平滑、回撤越小。
本策略在价格处于均线上方且UI低于其均线（风险降低）时做多。

参数:
- n: 周期 (推荐 14)
"""

from cta_api.function import *
import pandas as pd
import numpy as np

def signal(df, para=[14], proportion=1, leverage_rate=1):
    n = para[0]
    
    # 1. 计算 n 周期内的最高收盘价
    df['max_close'] = df['close'].rolling(window=n).max()
    
    # 2. 计算回撤百分比 (Percentage Drawdown)
    # R = 100 * (Close - MaxClose) / MaxClose
    df['pct_dd'] = 100 * (df['close'] - df['max_close']) / df['max_close']
    
    # 3. Squared Drawdown
    df['dd_sq'] = df['pct_dd'] ** 2
    
    # 4. Ulcer Index = Sqrt(Mean(Squared Drawdown))
    df['ui'] = np.sqrt(df['dd_sq'].rolling(window=n).mean())
    
    # 辅助均线
    df['ma'] = df['close'].rolling(window=n).mean()
    df['ui_ma'] = df['ui'].rolling(window=n).mean()
    
    # 策略逻辑
    # 做多: 价格 > MA 且 UI < UI_MA (趋势向上且风险在降低)
    condition_long = (df['close'] > df['ma']) & (df['ui'] < df['ui_ma'])
    
    # 做空: 价格 < MA 且 UI > UI_MA (趋势向下且风险/恐慌在增加)? 
    # 或者 UI开始升高预示顶部?
    # 简单的反向逻辑: 价格跌破MA
    condition_short = (df['close'] < df['ma'])
    
    # 信号生成
    df.loc[condition_long, 'pos'] = 1
    df.loc[condition_short, 'pos'] = -1
    df['pos'].fillna(0, inplace=True)
    
    # 构造 signal
    df['signal_long'] = np.nan
    df.loc[(df['pos'] == 1) & (df['pos'].shift(1) != 1), 'signal_long'] = 1
    df.loc[(df['pos'] != 1) & (df['pos'].shift(1) == 1), 'signal_long'] = 0
    
    df['signal_short'] = np.nan
    df.loc[(df['pos'] == -1) & (df['pos'].shift(1) != -1), 'signal_short'] = -1
    df.loc[(df['pos'] != -1) & (df['pos'].shift(1) == -1), 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['max_close', 'pct_dd', 'dd_sq', 'ui', 'ma', 'ui_ma', 'pos', 'signal_long', 'signal_short'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 20, 28]
    return [[p] for p in periods]
