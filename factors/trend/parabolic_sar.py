"""
Parabolic SAR抛物线转向策略

原理:
SAR跟踪止损点，形成抛物线。
SAR位于价格下方时做多，位于上方时做空，动态调整止损位。
经典趋势跟踪和止损工具。

时间周期推荐:
- 1H: step=0.02, max=0.2
- 4H: step=0.02, max=0.2
- 12H: step=0.01, max=0.2
- 24H: step=0.01, max=0.2

参数n范围: [(0.01, 0.02), (0.15, 0.20), (0.2, 0.2)]
"""

from cta_api.function import *
import numpy as np

def signal(df, para=[0.02, 0.2, 0.02], proportion=1, leverage_rate=1):
    step = para[0]
    max_val = para[1]
    af = para[2]

    df['sar'] = np.nan
    df['ep'] = df['high'].shift(1)
    df['trend'] = 0

    for i in range(2, len(df)):
        if df.loc[i, 'close'] > df.loc[i, 'ep']:
            df.loc[i, 'trend'] = 1
        elif df.loc[i, 'close'] < df.loc[i, 'ep']:
            df.loc[i, 'trend'] = 0

        if df.loc[i, 'trend'] == 1:
            df.loc[i, 'sar'] = df.loc[i, 'sar'] + step * (max_val - df.loc[i, 'sar'])
        else:
            df.loc[i, 'sar'] = df.loc[i, 'sar'] + step * (df.loc[i, 'ep'] - df.loc[i, 'sar'])

        if df.loc[i, 'trend'] == 1 and df.loc[i, 'low'] < df.loc[i, 'sar']:
            df.loc[i, 'trend'] = -1

    df['signal_long'] = np.where(df['close'] > df['sar'], 1, 0)
    df['signal_short'] = np.where(df['close'] < df['sar'], -1, 0)

    buy_signal = (df['signal_long'] == 1) & (df['signal_long'].shift(1) == 0)
    df.loc[buy_signal, 'signal_long'] = 1

    sell_signal = (df['signal_short'] == -1) & (df['signal_short'].shift(1) == 0)
    df.loc[sell_signal, 'signal_short'] = -1

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    df.drop(['sar', 'ep', 'trend', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    steps = [0.01, 0.02, 0.03, 0.04]
    max_vals = [0.15, 0.20, 0.25, 0.30]
    afs = [0.01, 0.02, 0.02, 0.03]

    para_list = []
    for step in steps:
        for max_val in max_vals:
            for af in afs:
                para_list.append([step, max_val, af])
    return para_list
