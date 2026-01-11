import os
import argparse
import requests
from datetime import datetime
from cta_api.binance_fetcher import collect, save_csv

def usdt_perpetual_symbols():
    r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=20)
    r.raise_for_status()
    info = r.json()
    syms = []
    for s in info.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            syms.append(s["symbol"])
    return syms

def run(interval="1h", start="2019-09-01", end=None, limit=None):
    end = end or datetime.utcnow().strftime("%Y-%m-%d")
    syms = usdt_perpetual_symbols()
    if limit:
        syms = syms[:limit]
    for sym in syms:
        try:
            df = collect(sym, interval, start, end)
            if df.empty:
                continue
            path = save_csv(df, interval, sym)
            print(path, len(df))
        except Exception as e:
            print(sym, "error", str(e))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", default="1h")
    ap.add_argument("--start", default="2019-09-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--limit", type=int, default=5, help="仅抓取前N个合约用于抽样")
    args = ap.parse_args()
    run(args.interval, args.start, args.end, args.limit)
