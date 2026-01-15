"""
Vortex涡流策略

原理:
Vortex基于价格波动计算涡流，识别趋势延续。
VR > 1表示趋势向上(买入)，VR < 1表示向下(卖出)。
基于价格高低点相对位置评估趋势。
适用于识别趋势转折点。

时间周期推荐:
- 1H: n=10-14
- 4H: n=10-20
- 12H: n=14-30
- 24H: n=14-40

参数n范围: [10, 14, 21]
"""

from cta_api.function import *

def signal(df, para=[14], proportion=1, leverage_rate=1):
    period = para[0]

    df['prev_close'] = df['close'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    df['prev_high'] = df['high'].shift(1)

    # Vortex Movement
    df['vm_plus'] = (df['high'] - df['prev_low']).abs()
    df['vm_minus'] = (df['low'] - df['prev_high']).abs()
    
    # True Range
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

    # Sum over period
    df['vm_plus_sum'] = df['vm_plus'].rolling(window=period).sum()
    df['vm_minus_sum'] = df['vm_minus'].rolling(window=period).sum()
    df['tr_sum'] = df['tr'].rolling(window=period).sum()

    # VI
    df['vi_plus'] = df['vm_plus_sum'] / df['tr_sum']
    df['vi_minus'] = df['vm_minus_sum'] / df['tr_sum']

    # Signal: VI+ > VI- => Long, VI+ < VI- => Short
    # Or cross
    
    condition_long = df['vi_plus'] > df['vi_minus']
    condition_short = df['vi_plus'] < df['vi_minus']

    df.loc[condition_long, 'signal_long'] = 1
    df.loc[~condition_long, 'signal_long'] = 0
    
    df.loc[condition_short, 'signal_short'] = -1
    df.loc[~condition_short, 'signal_short'] = 0

    df['signal'] = df['signal_long'] + df['signal_short']
    df['signal'] = df['signal'].replace(0, np.nan)

    df.drop(['prev_close', 'prev_low', 'prev_high', 'vm_plus', 'vm_minus', 'tr1', 'tr2', 'tr3', 'tr', 'vm_plus_sum', 'vm_minus_sum', 'tr_sum', 'vi_plus', 'vi_minus'], axis=1, inplace=True)

    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 21, 28]
    para_list = []
    for period in periods:
        para_list.append([period])
    return para_list
