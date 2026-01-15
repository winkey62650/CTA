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
import numpy as np
import pandas as pd

def signal(df, para=[20, 0.1], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [周期, 过程噪声]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """

    period = int(para[0])
    process_noise = float(para[1])

    # Kalman滤波参数
    delta = process_noise
    observation_noise = process_noise * (1 - delta)
    observation_cov = process_noise ** 2

    # 初始化数组以加速计算
    close_arr = df['close'].values
    n = len(df)
    
    kalman_estimate = np.zeros(n)
    kalman_error = np.zeros(n)
    kalman_gain = np.zeros(n)
    
    # 初始值
    kalman_estimate[0] = close_arr[0]
    kalman_error[0] = 1.0
    kalman_gain[0] = 0.0
    
    # 迭代计算Kalman估计 (Scalar loop)
    for i in range(1, n):
        # 预测
        # x_pred = x_prev
        # P_pred = P_prev + Q
        # 这里简化为：estimate_pred = estimate_prev (假设均值不变模型)
        # error_pred = error_prev + process_noise
        
        # 使用代码中的逻辑 (看起来像EMA变体?)
        # df.loc[df.index[i], 'kalman_estimate'] = df.loc[df.index[i], 'kalman_estimate'] + \
        #     df.loc[df.index[i], 'kalman_estimate'] - df['kalman_estimate'].shift(1) * delta
        # 这逻辑有点奇怪，重写为标准Kalman或保持意图但修复语法
        
        # 假设意图是标准一维Kalman Filter for constant position model
        prediction = kalman_estimate[i-1]
        prediction_error = kalman_error[i-1] + delta
        
        # 更新
        # K = P_pred / (P_pred + R)
        k = prediction_error / (prediction_error + observation_noise)
        kalman_gain[i] = k
        
        # x = x_pred + K * (z - x_pred)
        kalman_estimate[i] = prediction + k * (close_arr[i] - prediction)
        
        # P = (1 - K) * P_pred
        kalman_error[i] = (1 - k) * prediction_error

    df['kalman_estimate'] = kalman_estimate
    df['kalman_error'] = kalman_error

    # 计算偏离度
    # Avoid division by zero
    df['deviation'] = (df['close'] - df['kalman_estimate']) / df['kalman_error'].replace(0, 0.0001)

    # 做多信号: 价格显著低于Kalman估计
    condition1 = df['deviation'] < -2.0
    df.loc[condition1, 'signal_long'] = 1

    # 做多平仓信号: 价格回归到估计
    condition1 = df['deviation'].abs() < 1.0
    condition2 = df['deviation'].shift(1).abs() >= 1.0
    df.loc[condition1 & condition2, 'signal_long'] = 0

    # 做空信号: 价格显著高于Kalman估计
    condition1 = df['deviation'] > 2.0
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
    df.drop(['kalman_estimate', 'kalman_error', 'deviation', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 止盈止损
    df = process_stop_loss_close(df, proportion, leverage_rate=leverage_rate)

    return df


def para_list():
    """
    生成参数遍历列表
    """
    periods = [10, 20, 30]
    noises = [0.1, 0.05, 0.01]
    
    para_list = []
    for p in periods:
        for n in noises:
            para_list.append([p, n])
            
    return para_list
