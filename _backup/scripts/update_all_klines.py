import os
import requests
import pandas as pd
from datetime import datetime
from cta_api.binance_fetcher import collect
from config import root_path

def usdt_perpetual_symbols():
    r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30)
    r.raise_for_status()
    info = r.json()
    syms = []
    for s in info.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            syms.append(s["symbol"])
    return syms

def save_csv_update(df, interval, symbol):
    p = f"{root_path}/data/market_csv/{interval.upper()}"
    os.makedirs(p, exist_ok=True)
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    path = f"{p}/{s}.csv"
    if os.path.exists(path):
        old = pd.read_csv(path, parse_dates=["candle_begin_time"])
        merged = pd.concat([old, df], ignore_index=True)
        merged.drop_duplicates(subset=["candle_begin_time"], keep="last", inplace=True)
        merged.sort_values("candle_begin_time", inplace=True)
        merged.to_csv(path, index=False, encoding="utf-8")
    else:
        df.to_csv(path, index=False, encoding="utf-8")
    return path

def run(interval="1h"):
    end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    syms = usdt_perpetual_symbols()
    for sym in syms:
        s = sym.replace("USDT","-USDT")
        path = f"{root_path}/data/market_csv/{interval.upper()}/{s}.csv"
        if os.path.exists(path):
            try:
                last = pd.read_csv(path, usecols=["candle_begin_time"]).tail(1)["candle_begin_time"].iloc[0]
            except Exception:
                last = "2019-09-01"
        else:
            last = "2019-09-01"
        try:
            df = collect(sym, interval, last, end)
            if df.empty:
                continue
            p = save_csv_update(df, interval, sym)
            print(p, len(df))
        except Exception as e:
            print(sym, "error", str(e))

if __name__ == "__main__":
    run("1h")

