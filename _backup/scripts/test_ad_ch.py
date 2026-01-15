#!/usr/bin/env python3
import os
import sys
import pandas as pd
from pathlib import Path

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg
import scripts.prepare_feather_from_csv as conv

def test_ad_ch():
    try:
        factor_name = "breakout.ad_ch"
        symbol = "BTC-USDT"
        interval = "1H"
        para = 100
        
        # 确保数据存在
        s = symbol if "-" in symbol else symbol.replace("USDT", "-USDT")
        pkl = os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{s}.pkl")
        
        # 读取数据
        df = pd.read_feather(pkl)
        
        # 导入因子
        mod_name = f"factors.{factor_name}"
        cls = __import__(mod_name, fromlist=('',))
        
        print(f"因子模块: {cls}")
        print(f"signal 函数: {cls.signal}")
        
        # 调用 signal
        _df = df.copy()
        print(f"调用 signal: para={para}, proportion={cfg.proportion}, leverage_rate={cfg.leverage_rate}")
        _df = cls.signal(_df, para=para, proportion=cfg.proportion, leverage_rate=cfg.leverage_rate)
        
        print(f"结果列: {_df.columns.tolist()}")
        print(f"signal 列值: {_df['signal'].value_counts()}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ad_ch()