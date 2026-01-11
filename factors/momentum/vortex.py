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

    df['high_low'] = df['high'] - df['low']
    df['low_close'] =df['close'].shift(1)
    prev_close = df['close'].shift(2)

    df['up_move'] = df['high'].shift(1) > df['prev_close']
    df['down_move'] = df['low'].shift(1) < df['prev_close']

    df['vr'] = df['up_move'].rolling(window=period, min_periods=1).sum() / df['down_move'].rolling(window=period, min_periods=1).abs().sum()
    df['vr'] = df['vr'].rolling(window=period, min_periods=1).sum()

    df['vr_signal'] = np.where(df['vr'] > 1, 1, np.where(df['vr'] < 1, -1, 0))

    buy_signal = (df['vr_signal'] == 1) & (df['vr_signal'].shift(1) != 1)
    df.loc[buy_signal, 'signal_long'] = 1
    df.loc[df['vr_signal'] == -1, 'signal_long'] = 0

    sell_signal = (df['vr_signal'] == -1) & (df['vr_signal'].shift(1) != -1)
    df.loc[sell_signal, 'signal_short'] = -1
    df.loc[df['vr_signal'] == 1, 'signal_short'] = 0

    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    df['signal'] = df['signal'].replace(0, np.nan)

    df.drop(['high_low', 'low_close', 'prev_close', 'up_move', 'down_move', 'vr'], axis=1, inplace=True)
    
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)
    return df

def para_list():
    periods = [10, 14, 21, 28]
    para_list = []
    for period in periods:
        para_list.append([period])
    return para_list
