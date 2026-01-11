# CTA策略系统 - 参数优化和使用说明

## 目录
1. [系统架构](#系统架构)
2. [策略使用说明](#策略使用说明)
3. [参数优化方法](#参数优化方法)
4. [时间周期推荐](#时间周期推荐)
5. [参数遍历配置](#参数遍历配置)

---

## 系统架构

### 文件结构
```
Documents/Quant/CTA/
├── config.py                 # 全局配置文件
├── cta_api/                 # 核心API库
│   ├── function.py          # 信号生成函数
│   ├── evaluate.py          # 回测评估
│   └── binance_fetcher.py # 数据获取
├── factors/                 # 策略文件目录
│   ├── trend/              # 趋势跟踪策略 (25种)
│   ├── mean_reversion/     # 均值回归策略 (20种)
│   ├── momentum/           # 动量震荡策略 (18种)
│   ├── breakout/            # 突破策略 (10种)
│   ├── volume/             # 成交量策略 (11种)
│   └── STRATEGIES_OVERVIEW.md
```

### 策略文件标准接口

每个策略文件必须实现以下接口：

```python
from cta_api.function import *

def signal(df, para=[默认参数], proportion=1, leverage_rate=1):
    """
    :param df: 原始数据 (OHLCV)
    :param para: [策略参数列表]
    :param proportion: 止盈止损比例
    :param leverage_rate: 杠杆倍数
    :return: 包含signal的DataFrame
    """
    # 1. 计算技术指标
    # 2. 生成买卖信号
    # 3. 止盈止损处理
    return df


def para_list():
    """
    生成参数遍历列表

    :return: 参数列表，每个元素是参数组合
    """
    return [[para1], [para2], ...]
```

---

## 策略使用说明

### 1. 快速开始

#### 步骤1: 配置策略
编辑 `config.py`:
```python
# 交易标的
symbol_list = ['BTC-USDT']

# 策略名称（必须与factors目录下的策略文件名一致）
signal_name_list = ['sma']  # 或 'ema', 'rsi', 'macd', etc.

# 策略参数
para = [180]  # 根据策略类型调整

# 回测配置
date_start = '2021-01-01'
date_end = '2025-01-01'
c_rate = 8 / 10000  # 手续费
slippage = 1 / 1000  # 滑点
leverage_rate = 1  # 杠杆倍数

# 参数优化配置
per_eva = 'a'  # 全部遍历
del_mode = True  # 删除旧数据
cover_curve = False  # 是否绘制资金曲线
```

#### 步骤2: 运行回测
```bash
cd Documents/Quant/CTA
python 3_fastover.py
```

### 2. 策略分类详解

#### A. 趋势跟踪策略 (Trend Following) - 25种

**适用场景**: 单边趋势行情

**代表策略**:
1. **简单均线交叉**
   - `sma_cross.py` - 简单移动平均交叉
   - `ema_cross.py` - 指数移动平均交叉
   - `triple_ma.py` - 三重均线系统

2. **高级均线系统**
   - `macd.py` - MACD指标
   - `macd_zero.py` - MACD零轴策略
   - `macd_hist.py` - MACD柱状图
   - `hma.py` - 赫尔移动平均
   - `kama.py` - 自适应均线
   - `ichimoku_adv.py` - 一目均衡表

3. **通道突破**
   - `ma_band.py` - 多重均线带
   - `ma_envelope.py` - 移动平均包络
   - `donchian.py` - 唐奇通道
   - `turtle_trading.py` - 海龟交易
   - `linear_reg.py` - 线性回归
   - `price_channel.py` - 价格通道回归

**参数特点**: 大周期(20-100)，趋势确认机制

---

#### B. 均值回归策略 (Mean Reversion) - 20种

**适用场景**: 震荡市、区间震荡

**代表策略**:
1. **布林带系列**
   - `bb_mean_revert.py` - 布林带均值回归
   - `bb_breakout.py` - 布林带突破
   - `bb_width.py` - 布林带宽度
   - `bb_percentb.py` - 布林带%B
   - `bb_dynamic.py` - 动态布林带

2. **震荡指标**
   - `rsi_divergence.py` - RSI背离
   - `kdj.py` - 随机指标(KDJ)
   - `williams_r.py` - 威廉指标
   - `cci.py` - 商品通道指数
   - `cmo.py` - 钱德动量摆动
   - `ultimate_osc.py` - 最终震荡指标

3. **价格位置**
   - `quantile_revert.py` - 分位数回归
   - `kalman.py` - Kalman滤波
   - `hma_revert.py` - HMA均值回归
   - `atr_revert.py` - ATR均值回归

**参数特点**: 中小周期(5-40)，超买超卖确认

---

#### C. 动量震荡策略 (Momentum Oscillation) - 18种

**适用场景**: 趋势启动、动能判断

**代表策略**:
1. **动量类**
   - `momentum.py` - 基础动量
   - `roc.py` - 变化率
   - `trix.py` - 三重指数平滑

2. **震荡指标**
   - `rsi.py` - 相对强弱指标
   - `stochastic_osc.py` - 随机震荡指标
   - `dpo.py` - 去势价格震荡

3. **成交量和波动**
   - `bollinger_osc.py` - 布林带震荡
   - `chaikin_osc.py` - Chaikin振荡器
   - `mass_index.py` - 质量指数
   - `mfi.py` - 资金流量指数
   - `emv.py` - 便捷运动指标
   - `nvi.py` - 负量指标
   - `pvi.py` - 正量指标
   - `vma.py` - 可变移动平均

**参数特点**: 中等周期(10-30)，动能确认

---

#### D. 突破策略 (Breakout) - 10种

**适用场景**: 强趋势启动、关键价位突破

**代表策略**:
1. **价格突破**
   - `turtle_ch.py` - 海龟通道突破
   - `atr_ch.py` - ATR通道突破
   - `vol_break.py` - 波动率突破
   - `mean_break.py` - 均值突破
   - `fake_break.py` - 假突破过滤

2. **成交量确认突破**
   - `obv_ch.py` - OBV突破
   - `ad_ch.py` - A/D线突破
   - `vwap_ch.py` - VWAP突破
   - `vol_ma_ch.py` - 成交量均线突破

**参数特点**: 小周期(3-40)，突破确认机制

---

#### E. 成交量策略 (Volume-based) - 11种

**适用场景**: 资金流入流出判断、趋势确认

**代表策略**:
1. **资金流向**
   - `chaikin_osc.py` - Chaikin振荡器
   - `mfi.py` - 资金流量指数
   - `obv_ch.py` - 平衡成交量
   - `ad_ch.py` - 累积/派发线

2. **波动率**
   - `zero_osc.py` - 零轴震荡指标
   - `pos_neg.py` - 正负波动
   - `dx.py` - 动向指数
   - `rvi.py` - 相对波动率
   - `vwma_ch.py` - VWMA突破

**参数特点**: 多种周期组合(5-60)，多空动能分析

---

## 参数优化方法

### 1. 网格搜索 (Grid Search)

**适用场景**: 参数空间较小，计算资源充足

**实现方式**:
```python
# 在config.py中设置
per_eva = 'a'  # 全部遍历

# 在para_list()中定义参数网格
def para_list():
    return [
        [10, 20],      # 短期1
        [10, 25],      # 短期2
        [10, 30],      # 短期3
        [15, 40],      # 中期
        [20, 50],      # 长期
    ]
```

**优点**: 全面覆盖，找到全局最优解
**缺点**: 计算量大，时间消耗高

---

### 2. 随机搜索 (Random Search)

**适用场景**: 参数空间大，需要快速收敛

**实现方式**:
```python
import random

def para_list_random(n_samples=100):
    param_list = []
    for _ in range(n_samples):
        short = random.randint(5, 50)
        long = random.randint(20, 100)
        if short < long:
            param_list.append([short, long])
    return param_list
```

**优点**: 快速收敛，节省计算资源
**缺点**: 可能错过全局最优解

---

### 3. 贝叶斯优化 (Bayesian Optimization)

**适用场景**: 参数空间大，需要平衡探索和利用

**工具推荐**:
```bash
pip install optuna
```

**实现示例**:
```python
import optuna

def objective(trial):
    # 回测逻辑
    result = backtest(trial.suggest_int('period', 20))
    return result  # 最大化收益或夏普比率

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

**优点**: 高效利用历史信息，快速收敛
**缺点**: 需要额外库支持

---

### 4. 遗传算法 (Genetic Algorithm)

**适用场景**: 参数空间极大，多参数组合

**工具推荐**:
```bash
pip install deap
```

**实现思路**:
1. 初始化种群（100个个体）
2. 评估适应度（回测收益）
3. 选择（轮盘赌/锦标赛）
4. 交叉（单点/两点交叉）
5. 变异（随机扰动）
6. 迭代50-100代

**优点**: 并行搜索能力强
**缺点**: 实现复杂，需要调优

---

### 5. 遍历优化策略

根据市场特征选择遍历模式：

```python
# config.py
per_eva = 'a'  # 全部遍历 - 全面但不高效
per_eva = 'y'  # 按年遍历 - 适应周期性
per_eva = 'm'  # 按月遍历 - 中等粒度
per_eva = 'w'  # 按周遍历 - 细粒度，快速迭代
```

**推荐策略**:
- **趋势市场**: 使用'w'或'm'，适应趋势变化
- **震荡市场**: 使用'y'，捕捉长期均值
- **新策略开发**: 使用'a'，全面测试
- **生产环境**: 使用'w'，定期更新

---

## 时间周期推荐

### 币圈市场推荐

| 时间周期 | 推荐参数范围 | 适用策略类型 | 市场特征 |
|---------|--------------|------------|---------|
| **1H** | 5-15 | 动量、突破 | 高频波动，短周期调整 |
| **4H** | 10-40 | 趋势、震荡 | 中频波动，标准周期 |
| **12H** | 20-60 | 趋势、均值回归 | 低频波动，趋势确认 |
| **24H (日线)** | 30-100 | 长期趋势 | 长期趋势，大周期 |
| **1W (周线)** | 50-150 | 趋势、突破 | 长期趋势，周期稳定 |

### 股票市场推荐

| 时间周期 | 推荐参数范围 | 适用策略类型 | 市场特征 |
|---------|--------------|------------|---------|
| **日线** | 5-30 | 均值回归、震荡 | 日内波动，确认反转 |
| **周线** | 10-50 | 趋势、突破 | 中期趋势 |
| **月线** | 20-100 | 长期趋势 | 长期投资，大趋势 |

### 币圈 vs 股票差异

**币圈特点**:
- 24/7交易，高波动性
- 趋势延续性强
- 使用中长周期(12H-24H)

**股票特点**:
- 交易时间限制（4小时）
- 波动相对稳定
- 使用短中周期(日线-周线)
- 考虑股息、除权因素

---

## 参数遍历配置

### 快速遍历 (测试用)

```python
# config.py
per_eva = 'a'
para = [180]  # 默认参数
signal_name_list = ['sma']  # 测试单个策略
```

### 详细遍历 (实盘用)

```python
# config.py
per_eva = 'a'  # 全部遍历

# 在策略文件中定义详细参数网格
def para_list():
    return [
        [5, 10],      # 超短周期
        [5, 15],
        [5, 20],
        [10, 20],     # 短周期
        [10, 30],
        [10, 40],
        [15, 30],     # 中周期
        [15, 50],
        [20, 40],     # 长周期
        [20, 50],
        [20, 60],     # 超长周期
        [30, 60],
        [50, 100],    # 超长
    ]
```

### 分周期遍历

```python
# config.py
per_eva = 'm'  # 按月遍历

# 运行3次，测试不同时间段
# 第一次: 2021-01-01 ~ 2021-06-01
# 第二次: 2021-06-01 ~ 2021-12-01
# 第三次: 2021-12-01 ~ 2022-06-01
```

---

## 性能优化建议

### 1. 数据缓存

```python
# config.py
# 启用数据缓存
data_path = os.path.join(root_path, 'data/pickle_data')

# 第一次运行会下载并缓存
# 后续运行直接从缓存读取
```

### 2. 并行回测

```python
from multiprocessing import Pool

# 多进程并行跑不同参数组合
def backtest_parallel(param):
    return evaluate_strategy(param, df)

with Pool(processes=4) as p:
    results = p.map(backtest_parallel, param_list)
```

### 3. 增量优化

1. **粗粒度网格**: 初步筛选最优区域
2. **细粒度搜索**: 在最优区域精细搜索
3. **微调**: 最优参数±10%范围内微调

### 4. 避免过拟合

**方法**:
1. **时间切分**: 训练集(前70%) + 测试集(后30%)
2. **Walk Forward**: 滚动时间窗口验证
3. **样本外验证**: 在不同市场环境中测试

**指标**:
- 训练集夏普比率 > 2
- 测试集夏普比率 > 训练集的80%
- 最大回撤 < 30%

---

## 风险管理

### 1. 止盈止损配置

```python
# config.py
proportion = 0.5  # 50%止盈止损

# 策略内部
# process_stop_loss_close(df, proportion, leverage_rate)
# 多仓: 止盈价格 = 开仓价 × (1 + proportion)
#         止损价格 = 开仓价 × (1 - proportion)
# 空仓: 止盈价格 = 开仓价 × (1 - proportion)
#         止损价格 = 开仓价 × (1 + proportion)
```

### 2. 仓位管理

```python
# 基于ATR动态仓位
position_size = capital / (price * atr_multiplier * atr)

# 固定仓位
position_size = capital * leverage_rate / price

# 凯利公式
position_size = capital * win_rate / (loss_ratio - win_rate)
```

### 3. 风险控制

```python
# config.py
leverage_rate = 1  # 默认不使用杠杆
min_margin_ratio = 1 / 100  # 最低保证金率1%

# 最大回撤控制
max_drawdown = 0.3  # 最大回撤30%强制平仓
```

---

## 常见问题解答

### Q1: 如何选择策略类型？

**A**: 根据市场状态选择:
- **趋势市场**: 使用趋势跟踪、突破策略
- **震荡市场**: 使用均值回归、震荡指标
- **趋势启动**: 使用动量、成交量策略

判断市场状态:
1. ADX > 25 → 趋势市场
2. 布林带收缩 → 突破机会
3. RSI在40-60 → 震荡市场

### Q2: 参数范围如何设置？

**A**: 参考以下原则:
1. **短期策略**: 参数5-15
2. **中期策略**: 参数10-40
3. **长期策略**: 参数30-100
4. **震荡指标**: 参考经典值(RSI=14, KDJ=9)
5. **新参数**: 在经典值±50%范围内搜索

### Q3: 如何判断策略效果？

**A**: 关注以下指标:
1. **年化收益** > 20% 为优秀
2. **夏普比率** > 1.5 为优秀
3. **最大回撤** < 30% 为可控
4. **胜率** > 50% 为合理
5. **盈亏比** > 1.2 为优秀
6. **交易次数** > 30 次，保证统计显著性

### Q4: 策略失效怎么办？

**A**: 策略失效的表现:
1. 连续亏损 > 5笔
2. 最大回撤超过预期
3. 收益曲线持续走低

**应对措施**:
1. 暂停交易，复盘原因
2. 检查参数是否过拟合
3. 切换到适合当前市场的策略
4. 调整止盈止损比例
5. 缩减仓位规模

---

## 快速开始指南

### 5分钟快速上手

```python
# 1. 编辑config.py，设置基础参数
symbol_list = ['BTC-USDT']
signal_name_list = ['sma']
para = [180]
date_start = '2023-01-01'
date_end = '2024-01-01'

# 2. 运行回测
python 3_fastover.py

# 3. 查看结果
# 输出: 年化收益、夏普比率、最大回撤等
```

---

## 进阶技巧

### 1. 策略组合

**多信号过滤**:
```python
# 信号1: 趋势确认
# 信号2: 动量确认
# 信号3: 成交量确认
# 只有3个信号全部满足才开仓
```

### 2. 动态参数调整

```python
# 根据市场波动率动态调整参数
if volatility > high_threshold:
    use_short_term_parameters()
else:
    use_long_term_parameters()
```

### 3. 交易时间选择

**最佳交易时间**:
- 币圈: 避开欧美市场开盘重叠期(北京时间21:00-01:00)
- 股票: 交易前30分钟和后30分钟
- 夏季: 避开夏令时切换期

### 4. 多标的组合

**分散配置**:
- 不同币种(大中小盘)
- 不同板块(DeFi, L2, Layer1)
- 不同期限(短期、中期、长期)
- 对冲策略(多空平衡)

---

## 总结

本系统提供了88种交易策略，涵盖5大类别:
1. 趋势跟踪 (25种)
2. 均值回归 (20种)
3. 动量震荡 (18种)
4. 突破 (10种)
5. 成交量 (11种)

**最佳实践**:
1. 根据市场状态选择合适策略
2. 使用推荐的参数范围开始
3. 通过网格搜索找到最优参数
4. 严格控制风险，设置止盈止损
5. 定期回测，验证策略有效性
6. 避免过拟合，使用样本外验证

**快速开始**:
```bash
cd Documents/Quant/CTA
# 编辑config.py
python 3_fastover.py
```

祝交易顺利！
