"""
全面参数遍历分析
对所有策略进行参数网格搜索，找出参数高原和最优参数组合
"""

import os
import sys
importlib
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

# 添加路径
sys.path.insert(0, '/Users/winkey/Documents/Quant/CTA')

from cta_api.binance_fetcher import fetch_klines
from cta_api.function import process_stop_loss_close

class ParameterScan:
    """参数扫描器"""

    def __init__(self, data_path='data/pickle_data'):
        self.data_path = data_path

    def _scan_strategies(self):
        """扫描所有策略文件"""
        strategies = {}

        # 扫描所有策略目录
        strategy_categories = ['trend', 'mean_reversion', 'momentum', 'breakout', 'volume']

        for category in strategy_categories:
            path = f'actors/{category}'
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith('.py') and not file.startswith('__'):
                        strategy_name = file.replace('.py', '')
                        strategies[strategy_name] = {
                            'category': category,
                            'file': os.path.join(path, file)
                        }

        return strategies

    def get_strategy_params(self, strategy_name):
        """获取策略的参数列表"""
        try:
            # 策略文件直接在factors目录下，不在子目录中
            module_path = f'actors.{strategy_name.split("_")[0]}.{strategy_name}'
            module = importlib.import_module(module_path)
            if hasattr(module, 'para_list'):
                return module.para_list()
            return []
        except Exception as e:
            print(f"Error loading {strategy_name}: {e}")
            return []

    def backtest_single_strategy(self, strategy_name, params, symbol, start_date, end_date):
        """单个策略回测"""
        try:
            # 导入策略模块
            module_path = f'actors.{strategy_name.split("_")[0]}.{strategy_name}'
            module = importlib.import_module(module_path)
            
            # 获取数据
            df = fetch_klines(
                symbol=symbol,
                interval='1h',
                start=start_date,
                end=end_date
            )
            
            if df is None or len(df) == 0:
                return None

            # 生成信号
            df = module.signal(df, para=params)

            # 计算基础指标
            df['pos'] = 0
            df.loc[0, 'pos'] = 1

            # 简单计算持仓和盈亏
            for i in range(1, len(df)):
                if df['signal'].iloc[i] == 1 and df['pos'].iloc[i-1] != 1:
                    df.loc[df.index[i], 'pos'] = 1
                    entry_price = df['close'].iloc[i]
                elif df['signal'].iloc[i] == -1 and df['pos'].iloc[i-1] != -1:
                    df.loc[df.index[i], 'pos'] = -1
                    entry_price = df['close'].iloc[i]

            # 计算收益
            for i in range(1, len(df)):
                if df['pos'].iloc[i] == 0:
                    df.loc[df.index[i], 'pnl'] = 0
                elif df['pos'].iloc[i] == 1:
                    df.loc[df.index[i], 'pnl'] = df['close'].iloc[i] - df['close'].iloc[df['pos'][df['pos'] == 1].idxmax() - 1]
                elif df['pos'].iloc[i] == -1:
                    df.loc[df.index[i], 'pnl'] = df['close'].iloc[i] - df['close'].iloc[df['pos'][df['pos'] == -1].idxmax() - 1]

            # 计算累计净值
            df['equity'] = (1 + df['pnl'].cumsum())

            # 计算统计指标
            trades = df[df['pos'] != 0]
            win_trades = df[df['pnl'] > 0]

            if len(trades) > 0:
                # 年化收益
                annual_return = df['equity'].iloc[-1] ** (365 * 24 / len(df)) - 1

                # 夏普比率 (简化计算)
                returns = df['pnl'].values
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    sharpe_ratio = (mean_return / std_return) * np.sqrt(365 * 24)
                else:
                    sharpe_ratio = 0

                # 最大回撤
                cumulative_max = df['equity'].cummax()
                drawdown = cumulative_max - df['equity']
                max_drawdown = drawdown.max()

                # 胜率
                win_rate = len(win_trades) / len(trades) if len(trades) > 0 else 0

                # 盈亏比
                profit_sum = win_trades['pnl'].sum() if len(win_trades) > 0 else 0
                loss_sum = abs(trades[trades['pnl'] < 0]['pnl'].sum()) if len(trades[trades['pnl'] < 0].index.stop() else 0
                profit_loss_ratio = profit_sum / loss_sum if loss_sum > 0 else 0

                result = {
                    'strategy': strategy_name,
                    'params': str(params),
                    'annual_return': annual_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'profit_loss_ratio': profit_loss_ratio,
                    'total_trades': len(trades)
                }

                return result

            return None

        except Exception as e:
            print(f"Error backtesting {strategy_name} with {params}: {e}")
            return None

    def scan_all_strategies(self, symbol='BTC-USDT', start_date='2024-01-01', end_date='2024-03-01',
                          output_file='parameter_scan_results.csv'):
        """
        对所有策略进行参数扫描

        Args:
            symbol: 交易标的
            start_date: 开始日期
            end_date: 结束日期
            output_file: 结果输出文件
        """
        all_results = []
        total_strategies = len(self.strategies)

        print(f"开始扫描 {total_strategies} 个策略...")
        print(f"交易标的: {symbol}")
        print(f"时间范围: {start_date} ~ {end_date}")
        print("-" * 80)

        # 快速扫描：只扫描前3个策略，每个策略只扫描前3个参数
        quick_scan = list(self.strategies.keys())[:3]

        for idx, strategy_name in enumerate(tqdm(quick_scan, desc="策略扫描")):
            category = self.strategies[strategy_name]['category']

            print(f"\n[{idx+1}/{len(quick_scan)}] {category.upper()} - {strategy_name}")

            # 获取参数列表
            param_list = self.get_strategy_params(strategy_name)

            if not param_list:
                print(f"  无参数列表，跳过")
                continue

            print(f"  参数组合数: {len(param_list)}")

            # 对前3个参数组合进行回测
            for param in param_list[:3]:
                result = self.backtest_single_strategy(
                    strategy_name, param, symbol, start_date, end_date
                )

                if result:
                    all_results.append(result)

                print(f"  已扫描 {min(len(param_list), 3)} 个参数组合")

        # 保存结果
        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv(f'results/{output_file}', index=False)
            print(f"\n结果已保存到: results/{output_file}")

        # 分析结果
        self._analyze_results(all_results)

        print("\n" + "=" * 80)
        print("扫描完成！")
        print("=" * 80)

    def _analyze_results(self, results):
        """分析结果，找出参数高原"""
        if not results:
            print("没有结果可分析")
            return

        df = pd.DataFrame(results)

        print("\n" + "=" * 80)
        print("参数扫描分析报告")
        print("=" * 80)

        # 按策略分组分析
        strategy_summary = df.groupby('strategy').agg({
            'annual_return': ['mean', 'std', 'max', 'min'],
            'sharpe_ratio': ['mean', 'max'],
            'max_drawdown': ['min'],
            'win_rate': ['mean'],
            'total_trades': 'count'
        }).round(4)

        # 找出每个策略的最优参数
        best_params = df.loc[df.groupby('strategy')['annual_return'].idxmax()]
        best_params_sorted = best_params.sort_values('annual_return', ascending=False)

        print("\n策略排名 (按年化收益):")
        print(f"{'排名':<5} {'策略名称':<25} {'年化收益':>10} {'夏普':>8} {'最大回撤':<10} {'胜率':>8} {'参数'}")
        print("-" * 100)

        for i, (idx, row) in enumerate(best_params_sorted.head(10).iterrows():
            rank = i + 1
            print(f"{rank:2d} {row['strategy']:25} {row['annual_return']:>10.2%} {row['sharpe_ratio']:>8.2f} {row['max_drawdown']:>10.2%} {row['win_rate']:>8.1%} {row['params']}")

        # 参数高原分析
        print("\n参数高原分析:")
        print("-" * 80)

        plateau_analysis = {}
        for strategy in df['strategy'].unique():
            strategy_data = df[df['strategy'] == strategy]

            if len(strategy_data) < 2:
                continue

            # 计算参数高原
            mean_return = strategy_data['annual_return'].mean()
            plateau_params = strategy_data[strategy_data['annual_return'] >= mean_return * 0.9]

            if len(plateau_params) > 1:
                plateau_width = plateau_params['annual_return'].max() - plateau_params['annual_return'].min()
                plateau_width_pct = plateau_width / mean_return * 100

                plateau_analysis[strategy] = {
                    'mean_return': mean_return,
                    'max_return': strategy_data['annual_return'].max(),
                    'min_return': strategy_data['annual_return'].min(),
                    'std_return': strategy_data['annual_return'].std(),
                    'plateau_params_count': len(plateau_params),
                    'plateau_width': plateau_width,
                    'plateau_width_pct': plateau_width_pct,
                    'is_high_plateau': plateau_width_pct < 20  # 高原：宽度<20%
                }

        # 输出高原分析
        if plateau_analysis:
            print(f"{'策略名称':<25} {'平均收益':>10} {'最高收益':>10} {'最低收益':>10} {'标准差':>10} {'高原参数数':>5} {'高原宽度':>10} {'高原宽度%':>8} {'是否高原':<10}")
            print("-" * 100)

            for strategy, analysis in plateau_analysis.items():
                is_plateau = "是" if analysis['is_high_plateau'] else "否"
                print(f"{strategy:25} {analysis['mean_return']:>10.2%} {analysis['max_return']:>10.2%} {analysis['min_return']:>10.2%} {analysis['std_return']:>10.2f} {analysis['plateau_params_count']:>3d} {analysis['plateau_width']:>10.2%} {analysis['plateau_width_pct']:>8.1f} {is_plateau}")

        # 全局最优策略
        print("\n全局最优策略:")
        print("-" * 80)

        best_overall = df.loc[df['annual_return'].idxmax()]
        best_sharpe = df.loc[df['sharpe_ratio'].idxmax()]

        print(f"最高收益策略: {best_overall['strategy']}")
        print(f"  参数: {best_overall['params']}")
        print(f"  年化收益: {best_overall['annual_return']:.2%}")
        print(f"  夏普比率: {best_overall['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {best_overall['max_drawdown']:.2%}")
        print(f"  胜率: {best_overall['win_rate']:.1%}")

        print(f"\n最高夏普策略: {best_sharpe['strategy']}")
        print(f"  参数: {best_sharpe['params']}")
        print(f"  年化收益: {best_sharpe['annual_return']:.2%}")
        print(f"  夏普比率: {best_sharpe['sharpe_ratio']:.2f}")

        # 统计信息
        print("\n扫描统计:")
        print("-" * 80)
        print(f"总策略数: {df['strategy'].nunique()}")
        print(f"总参数组合数: {len(results)}")
        print(f"成功回测数: {df['annual_return'].notna().sum()}")
        print(f"平均年化收益: {df['annual_return'].mean():.2%}")
        print(f"平均夏普比率: {df['sharpe_ratio'].mean():.2f}")
        print(f"平均最大回撤: {df['max_drawdown'].mean():.2%}")


if __name__ == '__main__':
    scanner = ParameterScan()

    # 开始扫描
    scanner.scan_all_strategies(
        symbol='BTC-USDT',
        start_date='2024-01-01',
        end_date='2024-03-01'
    )
            if hasattr(module, 'para_list'):
                return module.para_list()
            return []
        except Exception as e:
            print(f"Error loading {strategy_name}: {e}")
            return []

    def backtest_single_strategy(self, strategy_name, params, symbol, start_date, end_date):
        """单个策略回测"""
        try:
            # 导入策略模块
            module = importlib.import_module(f'factors.{strategy_name.split("_")[0]}.{strategy_name}')
            
            # 获取数据
            df = fetch_klines(
                symbol=symbol,
                interval='1h',
                start=start_date,
                end=end_date
            )
            
            if df is None or len(df) == 0:
                return None

            # 生成信号
            df = module.signal(df, para=params)

            # 计算基础指标
            df['pos'] = 0
            df['pos'].iloc[0] = 1  # 初始持仓

            # 简单计算持仓和盈亏
            for i in range(1, len(df)):
                if df['signal'].iloc[i] == 1 and df['pos'].iloc[i-1] != 1:
                    df.loc[df.index[i], 'pos'] = 1
                    entry_price = df['close'].iloc[i]
                elif df['signal'].iloc[i] == -1 and df['pos'].iloc[i-1] != -1:
                    df.loc[df.index[i], 'pos'] = -1
                    entry_price = df['close'].iloc[i]
            
            # 计算收益
            for i in range(1, len(df)):
                if df['pos'].iloc[i] == 0:
                    df.loc[df.index[i], 'pnl'] = 0
                elif df['pos'].iloc[i] != df['pos'].iloc[i-1] and df['pos'].iloc[i-1] != 0:
                    if df['pos'].iloc[i] == 1:
                        df.loc[df.index[i], 'pnl'] = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
                    elif df['pos'].iloc[i] == -1:
                        df.loc[df.index[i], 'pnl'] = (df['close'].iloc[i-1] - df['close'].iloc[i]) / df['close'].iloc[i-1]

            # 计算累计净值
            df['equity'] = (1 + df['pnl']).cumprod()

            # 计算统计指标
            trades = df[df['pnl'] != 0]
            win_trades = df[df['pnl'] > 0]
            
            if len(trades) > 0:
                # 年化收益
                annual_return = df['equity'].iloc[-1] ** (365 * 24 / len(df)) - 1
                
                # 夏普比率 (简化计算)
                returns = df['pnl'].values
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    sharpe_ratio = (mean_return / std_return) * np.sqrt(365 * 24)
                else:
                    sharpe_ratio = 0

                # 最大回撤
                cumulative_max = df['equity'].cummax()
                drawdown = cumulative_max - df['equity']
                max_drawdown = drawdown.max()

                # 胜率
                win_rate = len(win_trades) / len(trades) if len(trades) > 0 else 0

                # 盈亏比
                profit_sum = win_trades['pnl'].sum() if len(win_trades) > 0 else 0
                loss_sum = abs(trades[trades['pnl'] < 0]['pnl'].sum()) if len(trades[trades['pnl'] < 0].index.stop() else 0)
                profit_loss_ratio = profit_sum / loss_sum if loss_sum > 0 else 0

                result = {
                    'strategy': strategy_name,
                    'params': str(params),
                    'annual_return': annual_return,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'profit_loss_ratio': profit_loss_ratio,
                    'total_trades': len(trades)
                }
                
                return result
            
            return None
            
        except Exception as e:
            print(f"Error backtesting {strategy_name} with {params}: {e}")
            return None

    def scan_all_strategies(self, symbol='BTC-USDT', start_date='2024-01-01', end_date='2024-03-01',
                          output_file='parameter_scan_results.csv'):
        """
        对所有策略进行参数扫描
        
        Args:
            symbol: 交易标的
            start_date: 开始日期
            end_date: 结束日期
            output_file: 结果输出文件
        """
        all_results = []
        total_strategies = len(self.strategies)
        
        print(f"开始扫描 {total_strategies} 个策略...")
        print(f"交易标的: {symbol}")
        print(f"时间范围: {start_date} ~ {end_date}")
        print("-" * 80)
        
        # 快速扫描：只扫描前3个策略，每个策略只扫描前5个参数
        quick_scan = list(self.strategies.keys())[:3]
        
        for idx, strategy_name in enumerate(tqdm(quick_scan, desc="策略扫描")):
            category = self.strategies[strategy_name]['category']
            
            print(f"\n[{idx+1}/{len(quick_scan)}] {category.upper()} - {strategy_name}")
            
            # 获取参数列表
            param_list = self.get_strategy_params(strategy_name)
            
            if not param_list:
                print(f"  无参数列表，跳过")
                continue
            
            print(f"  参数组合数: {len(param_list)}")
            
            # 对前5个参数组合进行回测
            for param in param_list[:5]:
                result = self.backtest_single_strategy(
                    strategy_name, param, symbol, start_date, end_date
                )
                
                if result:
                    all_results.append(result)
            
            print(f"  已扫描 {min(len(param_list), 5)} 个参数组合")
        
        # 保存结果
        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv(f'results/{output_file}', index=False)
            print(f"\n结果已保存到: results/{output_file}")
        
        # 分析结果
        self._analyze_results(all_results)
        
        print("\n" + "=" * 80)
        print("扫描完成！")
        print("=" * 80)

    def _analyze_results(self, results):
        """分析结果，找出参数高原"""
        if not results:
            print("没有结果可分析")
            return

        df = pd.DataFrame(results)
        
        print("\n" + "=" * 80)
        print("参数扫描分析报告")
        print("=" * 80)
        
        # 按策略分组分析
        strategy_summary = df.groupby('strategy').agg({
            'annual_return': ['mean', 'std', 'max', 'min'],
            'sharpe_ratio': ['mean', 'max'],
            'max_drawdown': ['min'],
            'win_rate': ['mean'],
            'total_trades': 'count'
        }).round(4)
        
        # 找出每个策略的最优参数
        best_params = df.loc[df.groupby('strategy')['annual_return'].idxmax()]
        best_params_sorted = best_params.sort_values('annual_return', ascending=False)
        
        print("\n策略排名 (按年化收益):")
        print(f"{'排名':<5} {'策略名称':<25} {'年化收益':>10} {'夏普':>8} {'最大回撤':<10} {'胜率':>8} {'参数'}")
        print("-" * 100)
        
        for i, (idx, row) in enumerate(best_params_sorted.head(10).iterrows()):
            rank = i + 1
            print(f"{rank:2d} {row['strategy']:25} {row['annual_return']:>10.2%} {row['sharpe_ratio']:>8.2f} {row['max_drawdown']:>10.2%} {row['win_rate']:>8.1%} {row['params']}")
        
        # 参数高原分析
        print("\n参数高原分析:")
        print("-" * 80)
        
        plateau_analysis = {}
        for strategy in df['strategy'].unique():
            strategy_data = df[df['strategy'] == strategy]
            
            if len(strategy_data) < 2:  # 需要至少3个参数点才能分析
                continue
            
            # 计算参数高原
            # 找出收益在平均值10%以内的所有参数组合
            mean_return = strategy_data['annual_return'].mean()
            plateau_params = strategy_data[strategy_data['annual_return'] >= mean_return * 0.9]
            
            if len(plateau_params) > 1:
                plateau_width = plateau_params['annual_return'].max() - plateau_params['annual_return'].min()
                plateau_width_pct = plateau_width / mean_return * 100
                
                plateau_analysis[strategy] = {
                    'mean_return': mean_return,
                    'max_return': strategy_data['annual_return'].max(),
                    'min_return': strategy_data['annual_return'].min(),
                    'std_return': strategy_data['annual_return'].std(),
                    'plateau_params_count': len(plateau_params),
                    'plateau_width': plateau_width,
                    'plateau_width_pct': plateau_width_pct,
                    'is_high_plateau': plateau_width_pct < 30  # 高原：宽度<30%
                }
        
        # 输出高原分析
        if plateau_analysis:
            print(f"{'策略名称':<25} {'平均收益':>10} {'最高收益':>10} {'最低收益':>10} {'标准差':>10} {'高原参数数':>5} {'高原宽度':>10} {'高原宽度%':>8} {'是否高原':<10}")
            print("-" * 100)
            
            for strategy, analysis in sorted(plateau_analysis.items(), key=lambda x: x[1]['plateau_width_pct'], reverse=False):
                is_plateau = "是" if analysis['is_high_plateau'] else "否"
                print(f"{strategy:25} {analysis['mean_return']:>10.2%} {analysis['max_return']:>10.2%} {analysis['min_return']:>10.2%} {analysis['std_return']:>10.2f} {analysis['plateau_params_count']:>3d} {analysis['plateau_width']:>10.2%} {analysis['plateau_width_pct']:>8.1f} {is_plateau}")
        
        # 全局最优策略
        print("\n全局最优策略:")
        print("-" * 80)
        
        best_overall = df.loc[df['annual_return'].idxmax()]
        best_sharpe = df.loc[df['sharpe_ratio'].idxmax()]
        
        print(f"最高收益策略: {best_overall['strategy']}")
        print(f"  参数: {best_overall['params']}")
        print(f"  年化收益: {best_overall['annual_return']:.2%}")
        print(f"  夏普比率: {best_overall['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {best_overall['max_drawdown']:.2%}")
        print(f"  胜率: {best_overall['win_rate']:.1%}")
        
        print(f"\n最高夏普策略: {best_sharpe['strategy']}")
        print(f"  参数: {best_sharpe['params']}")
        print(f"  年化收益: {best_sharpe['annual_return']:.2%}")
        print(f"  夏普比率: {best_sharpe['sharpe_ratio']:.2f}")
        
        # 统计信息
        print("\n扫描统计:")
        print("-" * 80)
        print(f"总策略数: {df['strategy'].nunique()}")
        print(f"总参数组合数: {len(results)}")
        print(f"成功回测数: {df['annual_return'].notna().sum()}")
        print(f"平均年化收益: {df['annual_return'].mean():.2%}")
        print(f"平均夏普比率: {df['sharpe_ratio'].mean():.2f}")
        print(f"平均最大回撤: {df['max_drawdown'].mean():.2%}")


if __name__ == '__main__':
    scanner = ParameterScan()
    
    # 创建results目录
    os.makedirs('results', exist_ok=True)
    
    # 开始扫描
    scanner.scan_all_strategies(
        symbol='BTC-USDT',
        start_date='2024-01-01',
        end_date='2024-03-01'
    )
