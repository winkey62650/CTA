#!/usr/bin/env python3
import os
import sys
import pandas as pd
from pathlib import Path

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg

def debug_ad_ch_full():
    factor_name = "breakout.ad_ch"
    symbol = "BTC-USDT"
    interval = "1H"
    para = [100]
    
    # 读取数据
    pkl = os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{symbol}.pkl")
    df = pd.read_feather(pkl)
    
    # 导入因子
    mod_name = f"factors.{factor_name}"
    cls = __import__(mod_name, fromlist=('',))
    
    # 调用 signal
    try:
        _df = cls.signal(df.copy(), para=para, proportion=cfg.proportion, leverage_rate=cfg.leverage_rate)
        print("✅ 成功")
        print(f"信号数量: {_df['signal'].notna().sum()}")
        print(f"信号值: {_df['signal'].value_counts()}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ad_ch_full()