import json
import os

def generate_report():
    with open('factor_metadata.json', 'r', encoding='utf-8') as f:
        factors = json.load(f)

    # Sort factors by name
    factors.sort(key=lambda x: x['name'])

    # Categorize
    factors_1_param = [f for f in factors if f['param_count'] == 1]
    factors_2_param = [f for f in factors if f['param_count'] == 2]
    factors_multi_param = [f for f in factors if f['param_count'] >= 3]

    markdown_content = "# 因子分析与参数平原查看器开发需求\n\n"
    
    # Section 1: Factor List
    markdown_content += "## 因子列表\n\n"
    markdown_content += "### 1. 单参数因子 (共 {} 个)\n".format(len(factors_1_param))
    for f in factors_1_param:
        markdown_content += f"#### {f['name']}\n"
        markdown_content += f"- **描述**: {f['description']}\n"
        markdown_content += f"- **参数数量**: {f['param_count']}\n"
        markdown_content += f"- **分类**: {f['category']}\n\n"

    markdown_content += "### 2. 双参数因子 (共 {} 个)\n".format(len(factors_2_param))
    for f in factors_2_param:
        markdown_content += f"#### {f['name']}\n"
        markdown_content += f"- **描述**: {f['description']}\n"
        markdown_content += f"- **参数数量**: {f['param_count']}\n"
        markdown_content += f"- **分类**: {f['category']}\n\n"

    markdown_content += "### 3. 多参数因子 (≥3) (共 {} 个)\n".format(len(factors_multi_param))
    for f in factors_multi_param:
        markdown_content += f"#### {f['name']}\n"
        markdown_content += f"- **描述**: {f['description']}\n"
        markdown_content += f"- **参数数量**: {f['param_count']}\n"
        markdown_content += f"- **分类**: {f['category']}\n\n"

    # Section 2: Market Applicability
    markdown_content += "## 市场适用性分析\n\n"
    markdown_content += "### 适用市场\n"
    markdown_content += "- **趋势型因子 (Trend/Momentum)** : 适用于单边上涨或下跌的强趋势行情，能够捕捉大幅波动带来的收益。\n"
    markdown_content += "- **震荡型因子 (Mean Reversion/Oscillator)** : 适用于横盘整理或宽幅震荡行情，利用价格回归均值的特性获利。\n"
    markdown_content += "- **突破型因子 (Breakout)** : 适用于波动率收缩后的变盘节点，能够捕捉新趋势的启动。\n"
    markdown_content += "- **成交量/波动率因子 (Volume/Volatility)** : 适用于高波动或成交活跃的市场，通常作为辅助确认信号。\n\n"

    markdown_content += "### 失效市场\n"
    markdown_content += "- **趋势型因子** : 在窄幅震荡或无序波动的市场中容易频繁止损 (Whipsaw)。\n"
    markdown_content += "- **震荡型因子** : 在单边强趋势中会过早逆势操作，导致大幅亏损 (被套)。\n"
    markdown_content += "- **突破型因子** : 在假突破频发的震荡市中容易产生连续亏损。\n\n"

    # Section 3: Parameter Plain Viewer Spec (Copied/Adapted from user input)
    markdown_content += "## 参数平原查看器开发规范\n\n"
    markdown_content += "### 单因子可视化要求\n"
    markdown_content += "- **图表类型**: 折线图\n"
    markdown_content += "- **X轴**: 因子参数值\n"
    markdown_content += "- **Y轴选项**: 收益率, 回撤比, 夏普率\n"
    markdown_content += "- **交互功能**: 动态切换Y轴指标, 参数范围调整\n\n"
    
    markdown_content += "### 双因子可视化要求\n"
    markdown_content += "- **图表类型**: 热力图\n"
    markdown_content += "- **X轴**: 因子参数1\n"
    markdown_content += "- **Y轴**: 因子参数2\n"
    markdown_content += "- **颜色映射**: 深色(高收益/高夏普) vs 浅色(低收益/低夏普)\n"
    markdown_content += "- **交互功能**: 动态调整热力指标, 范围缩放\n\n"

    # Section 4: Multi-factor Handling
    markdown_content += "## 多因子(≥3)处理方案\n\n"
    markdown_content += "### 多因子列表\n"
    for f in factors_multi_param:
        markdown_content += f"- {f['name']} ({f['param_count']} 个参数)\n"
    markdown_content += "\n"
    
    markdown_content += "### 降维方法\n"
    markdown_content += "1. **主成分分析 (PCA)**:\n"
    markdown_content += "   - **步骤**: 标准化参数空间 -> 计算协方差矩阵 -> 提取主成分 -> 投影到2D平面。\n"
    markdown_content += "   - **预期效果**: 将高维参数空间压缩至2维，保留大部分方差(信息量)，便于可视化寻找参数高原。\n\n"
    markdown_content += "2. **参数敏感性分析**:\n"
    markdown_content += "   - **流程**: 固定其他参数，轮询改变某一参数，计算目标函数(如夏普率)的变化率。\n"
    markdown_content += "   - **筛选标准**: 剔除敏感度过低(无效参数)或过高(不稳定参数)的维度，保留核心参数进行2D可视化。\n"

    with open('Factor_Analysis.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print("Factor_Analysis.md generated.")

if __name__ == "__main__":
    generate_report()
