import os
import pandas as pd
import importlib
import warnings
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from cta_api.base import BacktestConfig, BaseFactor
from cta_api.position import position_for_future
from cta_api.function import cal_equity_curve
from cta_api.statistics import transfer_equity_curve_to_trade, strategy_evaluate
from cta_api.draw_backtest_chart import draw_backtest_chart
from cta_api.logger import setup_logger

class BacktestEngine:
    """
    模块化 CTA 回测引擎
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.root_path = Path(__file__).parent.parent
        self.data_path = Path(config.data_path) if config.data_path else self.root_path / 'data/pickle_data'
        self.output_path = Path(config.output_path) if config.output_path else self.root_path / 'data/output'
        
        # 确保输出目录存在
        self.output_path.mkdir(parents=True, exist_ok=True)
        (self.output_path / 'equity_curve').mkdir(exist_ok=True)
        (self.output_path / 'charts').mkdir(exist_ok=True)

        # 初始化日志
        self.logger = setup_logger()

        # 加载最小下单量
        self.min_amount_dict = self._load_min_amount()

    def _load_min_amount(self) -> Dict[str, float]:
        """加载最小下单量配置"""
        csv_path = self.root_path / '最小下单量.csv'
        if not csv_path.exists():
            return {}
        
        try:
            df = pd.read_csv(csv_path, encoding='gbk')
            return dict(zip(df['合约'], df['最小下单量']))
        except Exception as e:
            self.logger.warning(f"Failed to load min amount: {e}")
            return {}

    def load_data(self, symbol: str, rule_type: str, offset: int = 0) -> pd.DataFrame:
        """读取并预处理数据"""
        file_path = self.data_path / rule_type / f'{symbol}.pkl'
        if not file_path.exists():
            raise FileNotFoundError(f"Data not found: {file_path}")
            
        df = pd.read_feather(file_path)
        
        # 基础处理
        if 'offset' not in df.columns:
            df['offset'] = 0
        if 'kline_pct' not in df.columns:
            df['kline_pct'] = pd.to_numeric(df['close'], errors='coerce').pct_change().fillna(0.0)
            
        df = df[df['offset'] == offset].copy()
        return df

    def run_backtest(self, 
                     symbol: str, 
                     factor_name: str, 
                     para: list, 
                     rule_type: str = '1H',
                     start_date: str = '2020-01-01',
                     end_date: str = '2099-01-01',
                     offset: int = 0,
                     show_chart: bool = False) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        运行单个回测
        :return: (df, metrics_df)
        """
        warnings.filterwarnings('ignore')
        self.logger.info(f"Start backtest: {symbol} | {factor_name} | {para}")
        
        # 1. 加载数据
        try:
            df = self.load_data(symbol, rule_type, offset)
        except Exception as e:
            self.logger.error(f"Error loading data for {symbol}: {e}")
            return None, None

        # 2. 计算信号 (动态加载策略)
        try:
            module = importlib.import_module(f'factors.{factor_name}')
            # 兼容旧模式 (module.signal) 和新模式 (module.Strategy class)
            if hasattr(module, 'Strategy') and issubclass(module.Strategy, BaseFactor):
                strategy = module.Strategy()
                df = strategy.signal(df, para, self.config.proportion, self.config.leverage_rate)
            elif hasattr(module, 'signal'):
                df = module.signal(df, para=para, proportion=self.config.proportion, leverage_rate=self.config.leverage_rate)
            else:
                raise ValueError(f"Invalid factor module: {factor_name}")
        except Exception as e:
            self.logger.error(f"Error executing factor {factor_name}: {e}")
            return None, None

        # 3. 计算持仓
        df = position_for_future(df)

        # 4. 时间过滤
        df = df[(df['candle_begin_time'] >= pd.to_datetime(start_date)) & 
                (df['candle_begin_time'] <= pd.to_datetime(end_date))]
        
        if df.empty:
            self.logger.warning(f"No data between {start_date} and {end_date}")
            return None, None

        # 5. 计算资金曲线
        min_amount = self.min_amount_dict.get(symbol, 0.001) # 默认值
        try:
            df = cal_equity_curve(
                df, 
                slippage=self.config.slippage, 
                c_rate=self.config.c_rate, 
                leverage_rate=self.config.leverage_rate, 
                min_amount=min_amount, 
                min_margin_ratio=self.config.min_margin_ratio
            )
        except Exception as e:
            self.logger.error(f"Error calculating equity: {e}")
            return None, None

        # 6. 结果统计
        final_equity = df.iloc[-1]['equity_curve']
        self.logger.info(f"[{symbol}] {factor_name} {para} Final Equity: {final_equity:.4f}")
        
        trade = transfer_equity_curve_to_trade(df)
        rtn, _ = strategy_evaluate(df.copy(), trade, rule_type)
        # 打印关键指标到日志
        self.logger.info(f"Metrics: Return={rtn.loc['年化收益', 0]}, Calmar={rtn.loc['年化收益/回撤比', 0]}, Sharpe={rtn.loc['夏普比率', 0]}, DD={rtn.loc['最大回撤', 0]}")

        # 7. 保存结果 & 画图
        self._save_results(df, symbol, factor_name, para, rule_type)
        
        if show_chart:
            chart_title = f"{symbol}_{factor_name}_{para}_{rule_type}"
            chart_path = self.output_path / 'charts' / f"{chart_title}.html"
            draw_backtest_chart(df, trade, path=str(chart_path), show=True, chart_title=chart_title, metrics=rtn)
            
        return df, rtn

    def _save_results(self, df: pd.DataFrame, symbol: str, factor_name: str, para: list, rule_type: str):
        """保存资金曲线CSV"""
        # 基础列
        base_cols = ['candle_begin_time', 'open', 'high', 'low', 'close', 'signal', 'pos', 
                'quote_volume', 'kline_pct', 'equity_curve']
        
        # 动态获取其他因子列 (排除已知的非因子列)
        exclude_cols = set(base_cols) | {'offset', 'start_time', 'equity_change', 'signal_', 'stop_loss_condition'}
        factor_cols = [c for c in df.columns if c not in exclude_cols]
        
        cols_to_save = [c for c in base_cols if c in df.columns] + factor_cols
        
        out_df = df[cols_to_save].copy()
        out_df.rename(columns={'equity_curve': 'r_line_equity_curve'}, inplace=True)
        
        filename = f"{factor_name}&{symbol.split('-')[0]}&{rule_type}&{str(para)}.csv"
        out_df.to_csv(self.output_path / 'equity_curve' / filename, index=False, encoding='gbk')
