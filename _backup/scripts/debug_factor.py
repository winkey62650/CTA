#!/usr/bin/env python3
import os
import sys
import pandas as pd
from pathlib import Path

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from config import root_path as project_root
import config as cfg

def debug_ad_ch():
    factor_name = "breakout.ad_ch"
    symbol = "BTC-USDT"
    interval = "1H"
    para = [100]  # 使用列表格式
    
    # 读取数据
    pkl = os.path.join(str(project_root), "data", "pickle_data", interval.upper(), f"{symbol}.pkl")
    df = pd.read_feather(pkl)
    
    print("原始数据列:", df.columns.tolist())
    print("数据形状:", df.shape)
    
    # 导入因子
    mod_name = f"factors.{factor_name}"
    cls = __import__(mod_name, fromlist=('',))
    
    # 手动执行因子代码来调试
    df_copy = df.copy()
    
    # 第32-34行
    high_low = df_copy['high'] - df_copy['low']
    close_open = df_copy['close'] - df_copy['open']
    df_copy['clv'] = ((close_open > 0) * high_low).abs()
    df_copy['clv'] = df_copy['clv'].where(close_open > 0, 0)
    
    print("创建的列 clv:", df_copy['clv'].notna().sum())
    
    # 第38行
    df_copy['ad'] = df_copy['clv'].cumsum()
    print("创建的列 ad:", df_copy['ad'].notna().sum())
    
    # 第41行
    period = para[0]
    df_copy['ad_ma'] = df_copy['ad'].rolling(window=period, min_periods=1).mean()
    
    # 第44-45行
    df_copy['price_high'] = df_copy['high'].rolling(window=period, min_periods=1).max()
    df_copy['price_low'] = df_copy['low'].rolling(window=period, min_periods=1).min()
    
    print("当前列:", df_copy.columns.tolist())
    
    # 尝试删除
    try:
        df_copy.drop(['high_low', 'close_open', 'clv', 'ad', 'ad_ma', 'price_high', 'price_low', 'signal_long', 'signal_short'], axis=1, inplace=True)
        print("删除成功")
    except Exception as e:
        print(f"删除失败: {e}")
        print("检查哪些列存在:")
        for col in ['high_low', 'close_open', 'clv', 'ad', 'ad_ma', 'price_high', 'price_low', 'signal_long', 'signal_short']:
            print(f"  {col}: {'存在' if col in df_copy.columns else '不存在'}")

if __name__ == "__main__":
    debug_ad_ch()