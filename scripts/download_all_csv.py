import os
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
    run("1h", "2019-09-01", None, limit=5)

