import os
import time
import requests
import pandas as pd
from datetime import datetime
from config import root_path

BASE = "https://fapi.binance.com"

def symbols():
    r = requests.get(f"{BASE}/fapi/v1/exchangeInfo", timeout=20)
    r.raise_for_status()
    info = r.json()
    out = []
    for s in info.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            out.append(s["symbol"])
    return out

def seed_last_month(symbol, period="1h"):
    r = requests.get(f"{BASE}/futures/data/openInterestHist", params={"symbol": symbol, "period": period, "limit": 500}, timeout=30)
    if r.status_code != 200:
        return pd.DataFrame()
    data = r.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    ts = df["timestamp"] if "timestamp" in df.columns else df["time"]
    df = pd.DataFrame({
        "candle_begin_time": pd.to_datetime(ts, unit="ms"),
        "open_interest": pd.to_numeric(df["sumOpenInterest"], errors="coerce") if "sumOpenInterest" in df.columns else pd.to_numeric(df["openInterest"], errors="coerce")
    })
    return df

def present_oi(symbol):
    r = requests.get(f"{BASE}/fapi/v1/openInterest", params={"symbol": symbol}, timeout=10)
    r.raise_for_status()
    j = r.json()
    t = pd.Timestamp.utcnow().floor("H")
    return pd.DataFrame([{"candle_begin_time": t, "open_interest": float(j["openInterest"])}])

def write_csv(path, df):
    if os.path.exists(path):
        old = pd.read_csv(path, parse_dates=["candle_begin_time"])
        all_df = pd.concat([old, df], ignore_index=True)
        all_df.drop_duplicates(subset=["candle_begin_time"], keep="last", inplace=True)
        all_df.sort_values("candle_begin_time", inplace=True)
        all_df.to_csv(path, index=False, encoding="utf-8")
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.sort_values("candle_begin_time", inplace=True)
        df.to_csv(path, index=False, encoding="utf-8")

def run(interval="1h"):
    out_dir = os.path.join(root_path, "data", "oi_history", interval.upper())
    os.makedirs(out_dir, exist_ok=True)
    syms = symbols()
    for s in syms:
        path = os.path.join(out_dir, f"{s.replace('USDT','-USDT')}_oi.csv")
        df = seed_last_month(s, period="1h")
        if not df.empty:
            write_csv(path, df)
    while True:
        for s in syms:
            path = os.path.join(out_dir, f"{s.replace('USDT','-USDT')}_oi.csv")
            try:
                df = present_oi(s)
                write_csv(path, df)
            except Exception:
                continue
        now = pd.Timestamp.utcnow()
        sleep_s = max(60, (now.ceil("H") - now).total_seconds())
        time.sleep(sleep_s)

if __name__ == "__main__":
    run("1h")

