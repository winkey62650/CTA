"""
简化的参数扫描脚本
对单个策略进行参数网格搜索，找出参数高原
"""

import os
import pandas as pd
import numpy as np

# 添加路径
sys.path.insert(0, '/Users/winkey/Documents/Quant/CTA')

# 简化的参数扫描器
class SimpleParamScanner:
    def __init__(self):
        print("=== 简化参数扫描器 ===")
        self.results = []

    def scan_strategy(self, strategy_path, param_grid):
        """扫描单个策略的参数"""
        print(f"\n扫描策略: {strategy_path}")

        # 读取策略文件内容
        with open(strategy_path, 'r', encoding='utf-8') as f:
            code = f.read()
        f.close()

        # 提取参数网格
        print(f"参数网格: {len(param_grid)} 个组合")
        print("-" * 80)

        # 这里应该调用策略的signal函数和evaluate函数
        # 由于依赖复杂，暂时只做参数分析框架
        print("注意: 此版本仅做参数扫描框架，需要完整的策略评估系统")

        return param_grid

    def analyze_parameter_sensitivity(self, results, param_grid):
        """分析参数敏感性"""
        if not results:
            return

        df = pd.DataFrame(results)

        print("\n参数敏感性分析:")
        print(f"  总参数数: {len(results)}")
        print(f"  平均收益: {df['annual_return'].mean():.2%}")
        print(f"  最高收益: {df['annual_return'].max():.2%}")
        print(f" 最低收益: {df['annual_return'].min():.2%}")
        print(f" 标准差: {df['annual_return'].std():.2%}")

        # 参数高原检测
        mean_return = df['annual_return'].mean()
        std_return = df['annual_return'].std()

        # 高原定义: 收益在平均值±1个标准差内
        plateau_high = mean_return + std_return
        plateau_low = mean_return - std_return

        plateau_params = df[
            (df['annual_return'] >= plateau_low) &
            (df['annual_return'] <= plateau_high)
        ]

        print(f"\n参数高原分析:")
        print(f"  高原范围: [{plateau_low:.2%}, {plateau_high:.2%}]")
        print(f"  高原内参数数: {len(plateau_params)}")
        print(f" 高原占比: {len(plateau_params)/len(results)*100:.1f}%")

        # 推荐参数
        if len(results) > 0:
            best = df.loc[df['annual_return'].idxmax()]
            print(f"\n推荐参数: {best['params']}")
            print(f"  年化收益: {best['annual_return']:.2%}")
            print(f"  夏普比率: {best.get('sharpe', 0):.2f}")
            print(f"  最大回撤: {best.get('max_drawdown', 0):.2%}")


if __name__ == '__main__':
    scanner = SimpleParamScanner()

    # 测试sma策略的参数网格
    test_params = [
        [5, 10],
        [5, 20],
        [10, 20],
        [10, 30],
        [20, 30]
    ]

    results = []
    for i, (short, long) in enumerate(test_params):
        result = {
            'strategy': 'sma',
            'params': f'[{short}, {long}]',
            'annual_return': 0.15 + i * 0.05,  # 模拟收益
            'sharpe_ratio': 1.2 + i * 0.1,
            'max_drawdown': 0.2 + i * 0.02
        }

        results.append(result)

    # 分析结果
    scanner.analyze_parameter_sensitivity(results, test_params)

    print("\n=== 扫描完成 ===")
