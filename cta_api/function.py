import os
import pandas as pd
import numpy as np
from typing import List, Union
try:
    import numba
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    print("Warning: Numba not found. Backtest speed might be slow. Please install numba: pip install numba")

def _process_stop_loss_core(
    open_arr: np.ndarray,
    close_arr: np.ndarray,
    signal_arr: np.ndarray,
    stop_loss_pct: float,
    leverage_rate: float
) -> tuple:
    """
    止损逻辑核心函数
    :return: (更新后的signal数组, stop_loss_condition数组)
    """
    length = len(open_arr)
    new_signal = signal_arr.copy()
    stop_loss_price_arr = np.full(length, np.nan)
    
    position = 0
    open_price = np.nan
    
    for i in range(length):
        # 1. 检查是否有新信号 (开仓或反手)
        curr_signal = new_signal[i]
        
        # 判断是否需要更新仓位：有信号，且 (还没开仓 或 信号方向改变)
        if not np.isnan(curr_signal):
            if np.isnan(open_price) or position != int(curr_signal):
                position = int(curr_signal)
                # 开仓价格: 下一根K线开盘价 (如果存在)，否则用当前收盘价
                if curr_signal != 0: # 开仓
                    if i < length - 1:
                        open_price = open_arr[i + 1]
                    else:
                        open_price = close_arr[i]
                else: # 平仓
                    open_price = np.nan
        
        # 2. 止损检查
        if position != 0:
            # 计算止损价
            stop_loss_price = open_price * (1 - position * stop_loss_pct / leverage_rate)
            stop_loss_price_arr[i] = stop_loss_price
            
            # 判断是否触发止损: (做多且收盘<止损) 或 (做空且收盘>止损)
            # 等价于: position * (close - stop_loss_price) <= 0
            if position * (close_arr[i] - stop_loss_price) <= 0:
                # 触发止损
                # 如果当前没有原始信号，则强制平仓 (写入0)
                if np.isnan(signal_arr[i]):
                    new_signal[i] = 0
                    position = 0
                    open_price = np.nan
                    
    return new_signal, stop_loss_price_arr

# 如果安装了 Numba，则进行 JIT 编译
if HAS_NUMBA:
    _process_stop_loss_optimized = numba.jit(nopython=True)(_process_stop_loss_core)
else:
    _process_stop_loss_optimized = _process_stop_loss_core



def transfer_to_period_data(df: pd.DataFrame, rule_type: str = '5T') -> pd.DataFrame:
    """
    将日线数据转换为相应的周期数据
    :param df: 原始数据
    :param rule_type: 转换周期 (e.g. '5T', '1H')
    :return: 转换后的周期数据 DataFrame
    """
    df = df.copy() # Avoid modifying original
    df.set_index('candle_begin_time', inplace=True)
    df['avg_price_1m'] = df['avg_price']
    agg_dict = {
        'symbol': 'first',
        'open':   'first',
        'high':   'max',
        'low':    'min',
        'close':  'last',
        'volume': 'sum',
        'quote_volume': 'sum',
        'trade_num':    'sum',
        'taker_buy_base_asset_volume':  'sum',
        'taker_buy_quote_asset_volume': 'sum',
        'avg_price': 'first'
    }
    # =====转换为其他分钟数据
    # Handle deprecated 'H' -> 'h'
    resample_rule = rule_type
    if resample_rule.endswith('H'):
        resample_rule = resample_rule.replace('H', 'h')

    period_df = df.resample(rule=resample_rule).agg(agg_dict)
    # =针对重采样后数据，补全空缺的数据。保证整张表没有空余数据
    period_df['symbol'].ffill(inplace=True)
    # 对开、高、收、低、价格进行补全处理
    period_df['close'].ffill(inplace=True)
    period_df['open'].fillna(value=period_df['close'], inplace=True)
    period_df['high'].fillna(value=period_df['close'], inplace=True)
    period_df['low'].fillna(value=period_df['close'],  inplace=True)
    # 将停盘时间的某些列，数据填补为0
    fill_0_list = ['volume', 'quote_volume', 'trade_num', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
    period_df.loc[:, fill_0_list] = period_df[fill_0_list].fillna(value=0)

    # 用1m均价代替重采样均价
    period_df['avg_price'] = df['avg_price_1m']
    period_df['avg_price'].fillna(value=period_df['open'], inplace=True)

    # 计算轮动所需要的每根k线涨跌幅
    df['pct'] = df['close'].pct_change(fill_method=None)
    df['pct'] = df['pct'].fillna(0)
    period_df_list = []
    # 通过持仓周期来计算需要多少个offset，遍历转换每一个offset数据
    try:
        range_limit = int(rule_type[:-1])
    except ValueError:
        range_limit = 1 # Fallback if rule_type is complex like '1D' (handle properly in real scenario)

    for offset in range(range_limit):
        period_df_resampled = df.resample(resample_rule, offset=offset).agg(agg_dict)
        period_df_resampled['kline_pct'] = df['pct'].resample(resample_rule, offset=offset).apply(lambda x: list(x))
        period_df_resampled['offset'] = offset
        period_df_resampled.reset_index(inplace=True)
        period_df_resampled.dropna(subset=['symbol'], inplace=True)
        period_df_list.append(period_df_resampled)
    
    # 将不同offset的数据，合并到一张表
    if period_df_list:
        period_df = pd.concat(period_df_list, ignore_index=True)
        period_df.sort_values(by='candle_begin_time', inplace=True)
        period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
        period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
        period_df.reset_index(inplace=True,drop=True)
    
    return period_df

# =====计算资金曲线
def cal_equity_curve(df: pd.DataFrame, 
                     slippage: float = 1 / 1000, 
                     c_rate: float = 5 / 10000, 
                     leverage_rate: float = 3,
                     min_amount: float = 0.01,
                     min_margin_ratio: float = 1 / 100) -> pd.DataFrame:
    """
    计算资金曲线
    :param df: 包含K线数据和pos列的DataFrame
    :param slippage: 滑点
    :param c_rate: 手续费率
    :param leverage_rate: 杠杆倍数
    :param min_amount: 最小下单量
    :param min_margin_ratio: 最低保证金率
    :return: 包含资金曲线的DataFrame
    """
    # =====下根k线开盘价
    df['next_open'] = df['open'].shift(-1)  # 下根K线的开盘价
    df['next_open'].fillna(value=df['close'], inplace=True)

    # =====找出开仓、平仓的k线
    condition1 = df['pos'] != 0  # 当前周期不为空仓
    condition2 = df['pos'] != df['pos'].shift(1)  # 当前周期和上个周期持仓方向不一样。
    open_pos_condition = condition1 & condition2

    condition1 = df['pos'] != 0  # 当前周期不为空仓
    condition2 = df['pos'] != df['pos'].shift(-1)  # 当前周期和下个周期持仓方向不一样。
    close_pos_condition = condition1 & condition2

    # =====对每次交易进行分组
    df.loc[open_pos_condition, 'start_time'] = df['candle_begin_time']
    df['start_time'].ffill(inplace=True)
    df.loc[df['pos'] == 0, 'start_time'] = pd.NaT

    # =====开始计算资金曲线
    initial_cash = 10000  # 初始资金，默认为10000元
    # ===在开仓时
    # 在open_pos_condition的K线，以开盘价计算买入合约的数量。（当资金量大的时候，可以用5分钟均价）
    df.loc[open_pos_condition, 'contract_num'] = initial_cash * leverage_rate / (min_amount * df['open'])
    df['contract_num'] = np.floor(df['contract_num'])  # 对合约张数向下取整
    # 开仓价格：理论开盘价加上相应滑点
    df.loc[open_pos_condition, 'open_pos_price'] = df['open'] * (1 + slippage * df['pos'])
    # 开仓之后剩余的钱，扣除手续费
    df['cash'] = initial_cash - df['open_pos_price'] * min_amount * df['contract_num'] * c_rate  # 即保证金

    # ===开仓之后每根K线结束时
    # 买入之后cash，contract_num，open_pos_price不再发生变动
    for _ in ['contract_num', 'open_pos_price', 'cash']:
        df[_].ffill(inplace=True)
    df.loc[df['pos'] == 0, ['contract_num', 'open_pos_price', 'cash']] = None

    # ===在平仓时
    # 平仓价格
    df.loc[close_pos_condition, 'close_pos_price'] = df['next_open'] * (1 - slippage * df['pos'])
    # 平仓之后剩余的钱，扣除手续费
    df.loc[close_pos_condition, 'close_pos_fee'] = df['close_pos_price'] * min_amount * df['contract_num'] * c_rate

    # ===计算利润
    # 开仓至今持仓盈亏
    df['profit'] = min_amount * df['contract_num'] * (df['close'] - df['open_pos_price']) * df['pos']
    # 平仓时理论额外处理
    df.loc[close_pos_condition, 'profit'] = min_amount * df['contract_num'] * (df['close_pos_price'] - df['open_pos_price']) * df['pos']
    # 账户净值
    df['net_value'] = df['cash'] + df['profit']

    # ===计算爆仓
    # 至今持仓盈亏最小值
    df.loc[df['pos'] == 1, 'price_min'] = df['low']
    df.loc[df['pos'] == -1, 'price_min'] = df['high']
    df['profit_min'] = min_amount * df['contract_num'] * (df['price_min'] - df['open_pos_price']) * df['pos']
    # 账户净值最小值
    df['net_value_min'] = df['cash'] + df['profit_min']
    # 计算保证金率
    df['margin_ratio'] = df['net_value_min'] / (min_amount * df['contract_num'] * df['price_min'])
    # 计算是否爆仓
    df.loc[df['margin_ratio'] <= (min_margin_ratio + c_rate), '是否爆仓'] = 1

    # ===平仓时扣除手续费
    df.loc[close_pos_condition, 'net_value'] -= df['close_pos_fee']
    # 应对偶然情况：下一根K线开盘价格价格突变，在平仓的时候爆仓。此处处理有省略，不够精确。
    df.loc[close_pos_condition & (df['net_value'] < 0), '是否爆仓'] = 1

    # ===对爆仓进行处理
    df['是否爆仓'] = df.groupby('start_time')['是否爆仓'].ffill()
    df.loc[df['是否爆仓'] == 1, 'net_value'] = 0

    # =====计算资金曲线
    df['equity_change'] = df['net_value'].pct_change(fill_method=None)
    df.loc[open_pos_condition, 'equity_change'] = df.loc[open_pos_condition, 'net_value'] / initial_cash - 1  # 开仓日的收益率
    df['equity_change'].fillna(value=0, inplace=True)
    df['equity_curve'] = (1 + df['equity_change']).cumprod()

    # =====删除不必要的数据，并存储
    df.drop(['next_open', 'contract_num', 'open_pos_price', 'cash', 'close_pos_price', 'close_pos_fee',
             'profit', 'net_value', 'price_min', 'profit_min', 'net_value_min', 'margin_ratio', '是否爆仓'],
            axis=1, inplace=True)

    return df



def process_stop_loss_close(df: pd.DataFrame, stop_loss_pct: float, leverage_rate: float) -> pd.DataFrame:
    """
    止损函数 (优化版)
    :param df:
    :param stop_loss_pct: 止损比例
    :param leverage_rate: 杠杆倍数
    :return:
    """
    # 准备 Numba 需要的 Numpy 数组
    # 注意：Numba 处理 NaN 需要 float 类型
    open_arr = df['open'].values.astype(np.float64)
    close_arr = df['close'].values.astype(np.float64)
    
    # 确保 signal 列存在且为 float 类型 (包含 NaN)
    if 'signal' not in df.columns:
        df['signal'] = np.nan
    signal_arr = df['signal'].values.astype(np.float64)
    
    # 调用 Numba 加速函数 (或纯 Python 函数)
    new_signal, stop_loss_price_arr = _process_stop_loss_optimized(
        open_arr, close_arr, signal_arr, stop_loss_pct, leverage_rate
    )
    
    # 将结果写回 DataFrame
    df['signal'] = new_signal
    df['stop_loss_condition'] = stop_loss_price_arr
    
    return df

def write_file(content: str, path: str):
    """
    写入文件
    :param content: 写入内容
    :param path: 文件路径
    :return:
    """
    with open(path, 'w', encoding='utf8') as f:
        f.write(content)


def num_to_pct(value: float) -> str:
    """将数字转为百分数"""
    return '%.2f%%' % (value * 100)


def generate_fibonacci_sequence(min_number: float, max_number: float) -> List[float]:
    """
    生成费拨那契数列，支持小数的生成
    :param min_number: 最小值
    :param max_number: 最大值
    :return:
    """
    sequence = []
    base = 1
    if min_number < 1:
        base = 10 ** len(str(min_number).split('.')[1])
    last_number = 0
    new_number = 1
    while True:
        last_number, new_number = new_number, last_number + new_number
        if new_number / base > min_number:
            sequence.append(new_number / base)
        if new_number / base > max_number:
            break
    return sequence[:-1]

def revise_data_length(data: pd.Series, data_len: int) -> pd.Series:
    """
    校正数据长度
    :param data: 原数据
    :param data_len: 资金曲线的数据长度
    :return: 校正后的数据
    """
    if len(data) > data_len:
        data = data[0:data_len]
    elif len(data) < data_len:
        data = pd.concat([data, pd.Series([0] * (data_len - len(data)))], ignore_index=True)

    return data

def get_benchmark(start_date: str, end_date: str, freq: str) -> pd.DataFrame:
    """获取基准时间序列"""
    benchmark = pd.DataFrame(pd.date_range(start=start_date, end=end_date, freq=freq))
    benchmark.rename(columns={0: 'candle_begin_time'}, inplace=True)
    return benchmark
