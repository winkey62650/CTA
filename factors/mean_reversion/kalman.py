"""
Kalman滤波均值回归策略 (Kalman Filter Mean Reversion)

原理:
Kalman滤波是一种贝叶斯滤波方法，能够实时估计价格的真实均值。
当价格偏离Kalman估计的均值时，预期价格会回归到均值。
价格低于Kalman估计时做多(超卖反弹)，高于时做空(超买回调)。
价格回归到均值附近时平仓。

时间周期推荐:
- 1H: n=10-30
- 4H: n=15-40

参数范围:
- n (周期): [10, 15, 20, 25, 30, 40]
- process_noise (过程噪声): [0.1, 0.05, 0.01, 0.001]
"""

from cta_api.function import *

def signal(df, para=[20, 0.1], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 过程噪声]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = para[0]
    process_noise = para[1]

    # Kalman滤波参数
    delta = process_noise
    observation_noise = process_noise * (1 - delta)
    observation_cov = process_noise ** 2

    # 初始化Kalman滤波器
    df['kalman_estimate'] = df['close']
    df['kalman_error'] = df['kalman_estimate'] * 0 + 0.01
    df['kalman_gain'] = df['kalman_error'] * 0

    # 迭代计算Kalman估计
    for i in range(len(df)):
        # 预测
        df.loc[df.index[i], 'kalman_estimate'] = df.loc[df.index[i], 'kalman_estimate'] + \
            df.loc[df.index[i], 'kalman_estimate'] - df['kalman_estimate'].shift(1) * delta

        # 更新误差和协方差
        df.loc[df.index[i], 'kalman_error'] = (1 - delta) * df.loc[df.index[i], 'kalman_error'] + \
                observation_cov * df.loc[df.index[i], 'kalman_error'].shift(1)

        # 更新增益
        df.loc[df.index[i], 'kalman_gain'] = df.loc[df.index[i], 'kalman_gain'] + delta * \
                observation_cov * df.loc[df.index[i], 'kalman_gain'].shift(1)

        # 稳定性
        df.loc[df.index[i], 'kalman_error'] = df.loc[df.index[i], 'kalman_error'] * (1 - delta) * 0.01

    # 计算偏离度
    df['deviation'] = (df['close'] - df['kalman_estimate']) / df['kalman_error']

    # 做多信号: 价格显著低于Kalman估计
    condition1 = df['deviation'] < -2 0
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格回归到估计
    condition1 = df['deviation'].abs() < 1 0
    condition2 = df['deviation'].shift(1).abs() >= 1.0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格显著高于Kalman估计
    condition1 = df['deviation'] > 2 0
    df.loc[condition1, 'signal_short'] = -1

    # 做空平仓信号: 价格回归到估计
    condition1 = df['deviation'].abs() < 1.0
    condition2 = df['deviation'].shift(1).abs() >= 1.0
    df.loc[condition1 & condition2, 'signal_short'] = 0

    # 合并多空信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 删除中间变量
    df.drop(['kalman_estimate', 'kalman_error', 'kalman_gain', 'deviation', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表

    参数组合:
    - 周期: 10, 15, 20, 25, 30, 40
    - 过程噪声: 0.1, 0.05, 0.01, 0.001
    """
    periods = [10, 15, 20, 25, 30, 40]
    noises = [0.1, 0.05, 0.01, 0.001]

    para_list = []
    for period in periods:
        for noise in noises:
            para_list.append([period, noise])

    return para_list
