# CTA 框架使用说明

## 环境准备
- Python 3.9+，推荐使用虚拟环境
- 安装依赖：`pip install -r requirements.txt`

## 下载数据
- 全市场 USDT 永续（周期 1h，跳过 OI）：
  - 运行：`python cta_api/binance_fetcher.py`
  - 输出：`data/market_csv/1H/{SYMBOL}.csv`
- 指定合约快速下载：`python cta_api/binance_fetcher.py BTCUSDT 1h 2025-12-15 2026-01-01`

## 转换数据供回测
- 将 CSV 转换为回测所需 feather：`python scripts/prepare_feather_from_csv.py BTCUSDT 1h`
  - 输出：`data/pickle_data/1H/BTC-USDT.pkl`

## 运行回测
- 快速回测：`python 2_fast_backview.py`
- 参数遍历：`python 3_fastover.py`
- 评估报告：`python 4_strategy_evaluate.py`

## 同步到 GitHub
- 首次初始化：`bash scripts/sync_to_github.sh init`
- 后续同步：`bash scripts/sync_to_github.sh push "update: data & scripts"`

