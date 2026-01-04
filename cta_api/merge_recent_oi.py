import pandas as pd
import os
from cta_api.binance_fetcher import save_recent_oi_csv
from config import root_path

def merge_recent(symbol: str, interval: str = "1h", hours: int = 480):
    base_path = os.path.join(root_path, "data/market_csv", interval.upper(), f"{symbol.replace('USDT','-USDT')}.csv")
    if not os.path.exists(base_path):
        print("base csv not found:", base_path)
        return
    recent_path = save_recent_oi_csv(symbol, interval, hours)
    base = pd.read_csv(base_path, parse_dates=["candle_begin_time"])
    recent = pd.read_csv(recent_path, parse_dates=["candle_begin_time"])
    cols = ["open_interest", "funding_rate"]
    merged = base.merge(recent[["candle_begin_time"] + cols], on="candle_begin_time", how="left", suffixes=("", "_recent"))
    for c in cols:
        merged[c] = merged[c].where(~merged[c].isna(), merged[f"{c}_recent"])
        merged.drop(columns=[f"{c}_recent"], inplace=True)
    merged.to_csv(base_path, index=False, encoding="utf-8")
    print("updated:", base_path)

if __name__ == "__main__":
    merge_recent("BTCUSDT", "1h", 480)

