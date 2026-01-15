"""
DPO去势策略

原理:
基于平均方向指标(DMI)，衡量多空力量对比。
MI > 25为多方占优(买入)，MI < -25为空方占优(卖出)。
结合价格变动和成交量评估多空力量。
适用于识别多空力量变化。

时间周期推荐:
- 4H: n=10-20
- 12H: n=14-21
- 24H: n=14-28

参数n范围: [10, 14, 21]
"""

from cta_api.function import *

def signal(df, para=[14, 25], proportion=1, leverage_rate=1):
    period = para[0]
    buy_threshold = para[1]
    sell_threshold = -buy_threshold

    # Standard DMI Logic
    up = df['high'] - df['high'].shift(1)
    down = df['low'].shift(1) - df['low']

    df['dm_plus'] = np.where((up > down) & (up > 0), up, 0)
    df['dm_minus'] = np.where((down > up) & (down > 0), down, 0)

    df['sum_plus'] = df['dm_plus'].rolling(window=period, min_periods=1).sum()
    df['sum_minus'] = df['dm_minus'].rolling(window=period, min_periods=1).sum()

    df['mi'] = 100 * (df['sum_plus'] - df['sum_minus']) / (df['sum_plus'] + df['sum_minus'])
    df['mi_signal'] = np.where(df['mi'] > buy_threshold, 1, np.where(df['mi'] < sell_threshold, -1, 0))

    df['signal'] = df['mi_signal'].replace(0, np.nan).fillna(method='ffill')
    
    df.drop(['dm_plus', 'dm_minus', 'sum_plus', 'sum_minus', 'mi', 'mi_signal'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 21]
    thresholds = [15, 20, 25]
    
    para_list = []
    for period in periods:
        for threshold in thresholds:
            para_list.append([period, threshold])
    return para_list
