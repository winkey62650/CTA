from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class BacktestConfig:
    """
    回测配置类
    """
    # 交易参数
    c_rate: float = 8 / 10000  # 手续费
    slippage: float = 1 / 1000 # 滑点
    leverage_rate: float = 1.0 # 杠杆
    min_margin_ratio: float = 0.01 # 最低保证金率
    
    # 策略参数
    proportion: float = 1.0 # 止盈止损比例
    
    # 路径配置 (可选，可以在Engine中指定默认值)
    data_path: Optional[str] = None
    output_path: Optional[str] = None

class BaseFactor(ABC):
    """
    因子策略基类
    所有新的因子都应该继承此类
    """
    
    @abstractmethod
    def signal(self, df: pd.DataFrame, para: list, proportion: float, leverage_rate: float) -> pd.DataFrame:
        """
        计算信号
        :param df: K线数据
        :param para: 策略参数
        :param proportion: 止盈止损比例
        :param leverage_rate: 杠杆倍数
        :return: 包含 signal 列的 DataFrame
        """
        pass

    @abstractmethod
    def para_list(self) -> List[list]:
        """
        返回推荐的参数列表用于批量测试
        :return: [[p1, p2], [p3, p4]]
        """
        pass
