import sys
import os
import pandas as pd
import numpy as np
from config import root_path

def convert(symbol: str, interval: str):
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    src = os.path.join(root_path, "data", "market_csv", interval.upper(), f"{s}.csv")
    dst_dir = os.path.join(root_path, "data", "pickle_data", interval.upper())
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f"{s}.pkl")
    df = pd.read_csv(src, parse_dates=["candle_begin_time"])
    df["offset"] = 0
    df["kline_pct"] = pd.to_numeric(df["close"], errors="coerce").pct_change().fillna(0.0)
    cols = [
        "candle_begin_time","open","high","low","close","volume","quote_volume","trade_num",
        "taker_buy_base_asset_volume","taker_buy_quote_asset_volume","taker_sell_quote_asset_volume",
        "offset","kline_pct"
    ]
    df = df[cols]
    df.to_feather(dst)
    print("saved:", dst, len(df))

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    interval = sys.argv[2] if len(sys.argv) > 2 else "1h"
    convert(symbol, interval)

