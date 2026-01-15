# Crypto CTA 回测框架

这是一个面向币安 USDT 永续合约的 CTA 量化回测框架，包含：
- 行情数据下载与增量更新
- 单因子单币种回测与可视化
- 单因子多参数、多币种批量回测
- 完整的策略因子库和模块化回测引擎

核心目标：在本地快速完成从数据获取、策略开发，到批量参数扫描、结果导出的一整套流程。

---

## 1. 目录结构概览

```text
CTA/
├── 0_数据获取.py           下载/更新币安 K 线+持仓量+资金费率
├── 0_1_数据转换.py         CSV 转换为 Feather/PKL，便于快速读取
├── 1_单个回测.py           单币种单因子回测，侧重策略调试与看图
├── 2_批量回测.py           单因子多参数、多币种批量扫描
├── 3_全量因子回测.py       遍历因子库做扫描（预留）
├── 4_因子分析_可视化.py     因子表现可视化（预留）
├── 5_因子分析_深度.py       多维参数/深度分析（预留）
├── cta_api/                回测引擎、资金曲线、统计与画图模块
├── factors/                因子库（趋势/动量/均值回归/成交量等）
├── data/
│   ├── market_csv/         原始行情 CSV（按周期分目录，如 1H）
│   ├── pickle_data/        转换后的高效数据文件
│   └── output/             回测结果与图表
├── config.py               全局配置（币种池、时间区间、费用、参数等）
├── requirements.txt        Python 依赖列表
└── 最小下单量.csv           各合约最小下单量配置
```

---

## 2. 环境与安装

1. 安装 Python 版本：建议 Python 3.9+  
2. 安装依赖：

```bash
pip install -r requirements.txt
```

本项目默认使用本地数据，不需要交易所 API Key。  
数据来源为币安公开接口以及 Binance Vision 归档数据。

---

## 3. 配置说明（config.py）

项目绝大部分行为通过 [config.py](file:///Users/winkey/Documents/Quant/CTA/config.py) 配置：

- 回测相关
  - `symbol_list`: 批量回测用的合约池，例如 `['BTC-USDT', 'ETH-USDT', ...]`
  - `signal_name_list`: 默认因子名列表，例如 `['sma']`
  - `rule_type_list`: 回测周期，如 `['1H']`
  - `date_start` / `date_end`: 统一回测起止时间
  - `c_rate`, `slippage`, `leverage_rate`, `min_margin_ratio`, `proportion`: 手续费、滑点、杠杆、爆仓线、止盈止损等基础参数

- 数据下载（0_数据获取.py）
  - `data_fetch_interval`: K 线周期，如 `"1h"`, `"4h"`, `"1d"`
  - `data_fetch_start`: 下载开始时间，例如 `"2019-09-01"`
  - `data_fetch_end`: 下载结束时间，`None` 表示当前时间
  - `data_fetch_limit`: 只抓前 N 个合约（调试/限速用）
  - `data_fetch_workers`: 并行 worker 数，1 为串行
  - `data_fetch_symbol_delay`: 串行模式下不同合约之间的停顿秒数

- 数据转换（0_1_数据转换.py）
  - `data_convert_symbol`: 指定单个合约转换，`None` 表示批量
  - `data_convert_interval`: 对应的周期目录，如 `"1h"`
  - `data_convert_workers`: 并行转换进程数

- 单个回测（1_单个回测.py）
  - `single_symbol`: 单因子单币种回测的标的
  - `single_factor`: 因子路径，如 `"trend.ema_cross"`
  - `single_para`: 单因子参数列表，如 `[12, 26]`
  - `single_start` / `single_end`: 单次回测时间范围
  - `single_rule_type`: 如 `"1H"`

- 批量回测（2_批量回测.py）
  - `batch_use_factor_params`: 是否使用因子内自带 `para_list`
  - `batch_cpu`: 并行 CPU 数

---

## 4. 使用流程

### 4.1 下载与增量更新行情数据

脚本：[0_数据获取.py](file:///Users/winkey/Documents/Quant/CTA/0_数据获取.py)  
功能：自动从币安下载 USDT 永续合约的 K 线、持仓量、资金费率，并支持：
- 判断本地 CSV 是否连续
- 若不连续则重下
- 若连续则按最新时间做增量补全
- 遇到接口暂时无数据时采用指数退避重试

运行方式：

```bash
python 0_数据获取.py
```

周期、起止时间、合约数量等由 config.py 中的 `data_fetch_*` 配置控制。  
数据会存放在 `data/market_csv/{INTERVAL}/SYMBOL.csv`，例如：

```text
data/market_csv/1H/BTC-USDT.csv
```

### 4.2 CSV 转换为 Feather/PKL

脚本：[0_1_数据转换.py](file:///Users/winkey/Documents/Quant/CTA/0_1_数据转换.py)  
功能：把 `data/market_csv` 下的 CSV 转换为 `data/pickle_data` 下的高速数据文件，用于回测引擎读取。

运行方式：

```bash
python 0_1_数据转换.py
```

转换范围同样由 config.py 中的 `data_convert_*` 配置控制。

### 4.3 单个回测：调试一个策略

脚本：[1_单个回测.py](file:///Users/winkey/Documents/Quant/CTA/1_单个回测.py)  
逻辑：从 config.py 中读取单次回测配置，然后调用 `BacktestEngine` 执行，并绘制资金曲线等图表。

运行方式：

```bash
python 1_单个回测.py
```

关键配置：
- `single_symbol`
- `single_factor`（例如 `"trend.ema_cross"` 或 `"sma"`）
- `single_para`
- `single_start` / `single_end`

运行完成后，可在 `data/output/charts` 查看图表，在 `data/output/equity_curve` 等目录查看明细。

### 4.4 批量回测：多参数、多币种扫描

脚本：[2_批量回测.py](file:///Users/winkey/Documents/Quant/CTA/2_批量回测.py)  
逻辑：
- 使用 config.py 中的 `symbol_list` 作为币种池
- 使用 `signal_name_list[0]` 作为当前因子
- 参数来源：
  - 若 `batch_use_factor_params = True`，则使用因子内部的 `para_list`
  - 否则使用 `config.para`
- 对所有币种 × 参数组合并行跑回测，打印实时进度条
- 每个币种生成独立的结果文件和参数平原图

运行方式：

```bash
python 2_批量回测.py
```

输出结构示例：

```text
data/output/
├── sma--BTC-USDT/
│   ├── batch_results_sma--BTC-USDT_YYYYMMDD_HHMMSS.xlsx
│   └── 参数平原图（按指标绘制）
├── sma--ETH-USDT/
│   └── ...
└── charts/
    └── 单次回测生成的图表等
```

Excel 中包含不同参数组合下的年化收益、最大回撤、夏普比率等指标，方便筛选最优参数。

---

## 5. 因子开发约定

因子统一放在 [factors](file:///Users/winkey/Documents/Quant/CTA/factors) 目录下，可以按类型分类，例如：
- `trend/` 趋势类
- `momentum/` 动量类
- `mean_reversion/` 均值回归类
- `volume/` 成交量类
- `volatility/` 波动率类

框架当前支持两种写法：

1. 函数型因子：模块内提供 `signal(df, para, proportion, leverage_rate)`  
2. 类型因子：定义继承自 `BaseFactor` 的 `Strategy` 类，并实现 `signal`、`para_list` 等方法

批量回测会尝试：
- 如果模块内有 `Strategy` 且是 `BaseFactor` 子类，使用类方式调用
- 否则回退到 `signal` 函数

推荐在因子中提供 `para_list()`，用于给批量回测提供一组默认扫描参数。

---

## 6. 注意事项

- 数据周期：下载数据时使用的 `data_fetch_interval`（如 "1h"）需要与回测时的 `rule_type` 保持一致（例如 "1H" 对应 "1h"）。
- 时区：框架统一使用 UTC 时间，CSV 中的 `candle_begin_time` 为 UTC。
- 风险提示：本项目仅用于策略研究与教学，所有回测结果不构成任何投资建议。

准备上传到 GitHub 时，通常只需要：
1. 保留 `data/output` 中的示例结果，或全部清空 `data` 目录以减小仓库体积
2. 检查是否无敏感信息（例如不提交真实 API Key）
3. 附上本 README 作为项目说明
