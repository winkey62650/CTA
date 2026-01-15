import os
import pandas as pd

# 项目根目录，用于拼接各种数据路径
root_path = os.path.dirname(os.path.abspath(__file__))

# pickle_data 目录（feather/pkl 数据缓存目录），不存在则自动创建
data_path = os.path.join(root_path, 'data/pickle_data')
if os.path.exists(data_path) == False:
    os.makedirs(data_path)

# ------------------------------
# 回测基础配置（适用于 1/2/3/5 等脚本的默认行为）
# ------------------------------

# 回测币种池（批量回测、全量因子回测默认使用这批合约）
# symbol_list = ['RARE-USDT', ...]  # 可以切换成小币池
symbol_list = [
    'BTC-USDT',
    'ETH-USDT', 'SOL-USDT', 'XRP-USDT', 'DASH-USDT', 'ZEC-USDT', 'XMR-USDT',
    # 'BNB-USDT', 'DOGE-USDT', '1000PEPE-USDT', 'SUI-USDT', 'ADA-USDT', 'BCH-USDT',
    # 'LTC-USDT', 'LINK-USDT', 'AVAX-USDT', 'ZEN-USDT', 'FIL-USDT', 'NEAR-USDT',
    # 'AAVE-USDT', 'DOT-USDT', 'WIF-USDT', '1000BONK-USDT', 'DUSK-USDT', 'WLD-USDT',
    # 'CHZ-USDT', 'UNI-USDT', 'ICP-USDT', 'ARB-USDT', '1000SHIB-USDT',
]

# 通用策略参数池（2_批量回测.py 默认使用，单个回测也可从这里取第一个）
para = [*range(100, 1000, 10)]

# 止盈止损比例（大多数因子里作为 proportion 传入）
proportion = 0.5

# 默认因子列表（2_批量回测.py、1_单个回测.py 会取第一个作为默认策略）
# signal_name_list = ['rsinmapctv1', ...]
signal_name_list = ['sma']

# 默认回测周期列表（1H / 4H / 1D 等），脚本通常取第一个
rule_type_list = ['1H']

# 全局默认回测起止时间（大部分脚本都会读这个）
date_start = '2021-01-01'
date_end = '2025-01-01'

# K 线偏移（部分老逻辑使用，一般保持 0 即可）
offset = 0

# 手续费率（万分之 8）
c_rate = 8 / 10000

# 滑点设置（可以是比例，也可以根据需要改成固定点数）
slippage = 1 / 1000

# 杠杆倍数
leverage_rate = 1

# 最低保证金率，低于该值视为爆仓
min_margin_ratio = 1 / 100

# 是否按时间分区间遍历：y=按年，m=按月，w=按周，a=全部遍历
per_eva = 'a'

# 删除模式（老版本批量回测使用，控制是否清理旧文件）
del_mode = True

# 是否绘制参数覆盖总资金曲线（老版本可视化开关）
cover_curve = False

# 最小下单量表，读取 csv 后构建合约→最小下单量字典
min_amount_df = pd.read_csv(os.path.join(root_path, '最小下单量.csv'), encoding='gbk')
min_amount_dict = {}
for i in min_amount_df.index:
    min_amount_dict[min_amount_df.at[i, '合约']] = min_amount_df.at[i, '最小下单量']

# ------------------------------
# 0_数据获取.py 相关配置（行情+持仓+资金费率下载）
# ------------------------------

# 下载 K 线周期，如 "1h" / "4h" / "1d"
data_fetch_interval = "1h"

# 下载开始日期（字符串，可带时间）
data_fetch_start = "2019-09-01"

# 下载结束日期（None 表示当前时间）
data_fetch_end = None

# 每次只抓前 N 个合约（用于抽样和限速）
data_fetch_limit = 1000

# 下载并发数（1 表示串行，多于 1 使用 joblib 并行）
data_fetch_workers = 1

# 串行模式下，不同合约之间的停顿时间（秒）
data_fetch_symbol_delay = 0.2

# ------------------------------
# 0_1_数据转换.py 相关配置（CSV→Feather 转换）
# ------------------------------

# 单合约转换：如 "BTCUSDT" 或 "BTC-USDT"；None 表示批量转换整个目录
data_convert_symbol = None

# 转换的周期目录，如 "1h" 对应 data/market_csv/1H
data_convert_interval = "1h"

# 批量转换并发数
data_convert_workers = 4

# 是否跳过已存在的 pkl/feather 文件（True=跳过，False=强制重建）
data_convert_skip_existing = True

# ------------------------------
# 1_单个回测.py 相关配置（单策略可视化调试）
# ------------------------------

# 单次回测的交易对
single_symbol = "BTC-USDT"

# 单次回测的策略路径，如 "trend.ema_cross" 或 "breakout.ad_ch"
single_factor = "trend.ema_cross"

# 单次回测的参数列表，例如 [12, 26] 或 [20]
single_para = [12, 26]

# 单次回测起止时间
single_start = "2025-01-01"
single_end = "2026-01-01"

# 单次回测使用的周期（通常与 rule_type_list 对应）
single_rule_type = "1H"

# ------------------------------
# 2_批量回测.py 相关配置（单因子多参数、多币种扫描）
# ------------------------------

# 是否使用因子文件内自带的 para_list 作为参数网格
batch_use_factor_params = False

# 批量回测并行使用的 CPU 数量
batch_cpu = max(1, os.cpu_count() - 1)

# ------------------------------
# 3_全量因子回测.py 相关配置（遍历所有因子）
# ------------------------------

# 全量因子回测的标的
full_symbol = "BTC-USDT"

# 全量因子回测的周期（默认可与 rule_type_list 对齐）
full_rule_type = "1h"

# 全量因子回测起止时间（默认复用全局 date_start/date_end）
full_start = date_start
full_end = date_end

# 全量因子回测并行使用的 CPU 数
full_cpu = max(1, os.cpu_count() - 1)

# 限制任务数量（0 表示全部因子全部参数）
full_limit = 0

# 因子类别过滤，例如 "trend" 只跑趋势类因子，None 表示不过滤
full_category = None

# ------------------------------
# 5_因子分析_深度.py 相关配置（多维参数 + PCA 分析）
# ------------------------------

# 深度分析使用的因子路径
multi_factor_path = "momentum.macd"

# 深度分析使用的交易对
multi_factor_symbol = "BTC-USDT"

# 深度分析回测起止时间
multi_factor_start = "2023-01-01"
multi_factor_end = "2024-01-01"

# ------------------------------
# 通用 API 限速配置（所有 HTTP 请求的节奏控制）
# ------------------------------

# 单个 HTTP 请求之间的最小等待时间（秒）
api_request_sleep = 1.0

