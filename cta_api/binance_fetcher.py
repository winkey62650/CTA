import time
import math
import sys
import os
from typing import Optional
import requests
import pandas as pd
import numpy as np
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from config import root_path
from cta_api.binance_vision_fetcher import fetch_oi as vision_fetch_oi, fetch_funding as vision_fetch_funding
SKIP_OI = True

BASE = "https://fapi.binance.com"

def _to_ms(s: str) -> int:
    n = int(s[:-1])
    u = s[-1]
    if u == "m":
        return n * 60_000
    if u == "h":
        return n * 3_600_000
    if u == "d":
        return n * 86_400_000
    raise ValueError(s)

def _ts(x) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    if isinstance(x, str):
        return int(pd.Timestamp(x).value // 10**6)
    return int(pd.Timestamp(x).value // 10**6)

def fetch_klines(symbol: str, interval: str, start: str, end: str, limit: int = 1500) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    st = _ts(start)
    et = _ts(end)
    step = _to_ms(interval)
    rows = []
    while st < et:
        params = {"symbol": sym, "interval": interval, "startTime": st, "endTime": et, "limit": limit}
        r = requests.get(f"{BASE}/fapi/v1/klines", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        rows.extend(data)
        last = data[-1][0]
        st = last + step
        time.sleep(0.2)
    if not rows:
        return pd.DataFrame()
    arr = np.array(rows, dtype=object)
    df = pd.DataFrame(arr[:, :12], columns=[
        "open_time","open","high","low","close","volume","close_time","quote_asset_volume",
        "number_of_trades","taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"
    ])
    for c in ["open","high","low","close","volume","quote_asset_volume","taker_buy_base_asset_volume","taker_buy_quote_asset_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["candle_begin_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["taker_sell_quote_asset_volume"] = df["quote_asset_volume"] - df["taker_buy_quote_asset_volume"]
    df.rename(columns={
        "number_of_trades":"trade_num",
        "quote_asset_volume":"quote_volume",
    }, inplace=True)
    return df[[
        "candle_begin_time","open","high","low","close","volume","quote_volume","trade_num",
        "taker_buy_base_asset_volume","taker_buy_quote_asset_volume","taker_sell_quote_asset_volume"
    ]]

def _oi_period(interval: str) -> str:
    if interval.endswith("m"):
        m = int(interval[:-1])
        if m <= 5:
            return "5m"
        if m <= 15:
            return "15m"
        if m <= 30:
            return "30m"
        return "1h"
    if interval.endswith("h"):
        h = int(interval[:-1])
        if h <= 1:
            return "1h"
        if h <= 4:
            return "4h"
        return "1d"
    return "1h"

def fetch_open_interest_hist(symbol: str, interval: str, start: str, end: str, limit: int = 500) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    period = _oi_period(interval)
    st = _ts(start)
    et = _ts(end)
    rows = []
    cur = st
    while cur < et:
        params = {"symbol": sym, "period": period, "limit": limit, "startTime": cur, "endTime": et, "contractType": "PERPETUAL"}
        r = requests.get(f"{BASE}/futures/data/openInterestHist", params=params, timeout=30)
        if r.status_code >= 400:
            params = {"pair": sym, "period": period, "limit": limit, "startTime": cur, "endTime": et, "contractType": "PERPETUAL"}
            r = requests.get(f"{BASE}/futures/data/openInterestHist", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        rows.extend(data)
        nxt = int(data[-1]["timestamp"])
        if nxt <= cur:
            break
        cur = nxt + _to_ms(period)
        time.sleep(0.2)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "sumOpenInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["sumOpenInterest"], errors="coerce")
    elif "openInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["openInterest"], errors="coerce")
    else:
        df["open_interest"] = np.nan
    df["candle_begin_time"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["candle_begin_time","open_interest"]]

def fetch_open_interest_series(symbol: str, interval: str, start: str, end: str, limit: int = 500) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    st = _ts(start)
    et = _ts(end)
    rows = []
    cur = st
    while cur < et:
        params = {"symbol": sym, "period": interval, "contractType": "PERPETUAL", "limit": limit, "startTime": cur, "endTime": et}
        r = requests.get(f"{BASE}/futures/data/openInterest", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        rows.extend(data)
        nxt = int(data[-1]["timestamp"])
        if nxt <= cur:
            break
        cur = nxt + _to_ms(interval)
        time.sleep(0.2)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "sumOpenInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["sumOpenInterest"], errors="coerce")
    elif "openInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["openInterest"], errors="coerce")
    else:
        df["open_interest"] = np.nan
    df["candle_begin_time"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df[["candle_begin_time","open_interest"]]

def fetch_funding_rate(symbol: str, start: str, end: str, limit: int = 1000) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    st = _ts(start)
    et = _ts(end)
    rows = []
    cur = st
    while cur < et:
        params = {"symbol": sym, "limit": limit, "startTime": cur, "endTime": et}
        r = requests.get(f"{BASE}/fapi/v1/fundingRate", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        rows.extend(data)
        nxt = int(data[-1]["fundingTime"])
        if nxt <= cur:
            break
        cur = nxt + 1
        time.sleep(0.2)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["funding_rate"] = pd.to_numeric(df["fundingRate"], errors="coerce")
    df["funding_time"] = pd.to_datetime(df["fundingTime"], unit="ms")
    return df[["funding_time","funding_rate"]]

def collect(symbol: str, interval: str, start: str, end: str) -> pd.DataFrame:
    k = fetch_klines(symbol, interval, start, end)
    if k.empty:
        return k
    if SKIP_OI:
        oi = pd.DataFrame()
    else:
        try:
            oi = fetch_open_interest_hist(symbol, interval, start, end)
        except Exception:
            oi = pd.DataFrame()
        if oi.empty:
            try:
                oi = fetch_open_interest_series(symbol, interval, start, end)
            except Exception:
                oi = pd.DataFrame()
        if oi.empty:
            try:
                oi = vision_fetch_oi(symbol, interval, start, end)
            except Exception:
                oi = pd.DataFrame()
    try:
        fr = fetch_funding_rate(symbol, start, end)
    except Exception:
        fr = pd.DataFrame()
    if fr.empty:
        try:
            fr = vision_fetch_funding(symbol, start, end)
        except Exception:
            fr = pd.DataFrame()
    df = k.copy()
    if not oi.empty:
        df = pd.merge_asof(df.sort_values("candle_begin_time"), oi.sort_values("candle_begin_time"), on="candle_begin_time")
    else:
        df["open_interest"] = np.nan
    if not fr.empty:
        df = pd.merge_asof(df.sort_values("candle_begin_time"), fr.rename(columns={"funding_time":"candle_begin_time"}).sort_values("candle_begin_time"), on="candle_begin_time")
    else:
        df["funding_rate"] = np.nan
    return df

def save_csv(df: pd.DataFrame, interval: str, symbol: str) -> str:
    p = f"{root_path}/data/market_csv/{interval.upper()}"
    os.makedirs(p, exist_ok=True)
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    path = f"{p}/{s}.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    return path

def save_recent_oi_csv(symbol: str, interval: str, hours: int = 480) -> str:
    now = pd.Timestamp.utcnow()
    start = (now - pd.Timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    end = now.strftime("%Y-%m-%d %H:%M:%S")
    df = collect(symbol, interval, start, end)
    out_dir = f"{root_path}/data/oi_history/{interval.upper()}"
    os.makedirs(out_dir, exist_ok=True)
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    path = f"{out_dir}/{s}_oi_recent.csv"
    df[["candle_begin_time","open_interest"]].to_csv(path, index=False, encoding="utf-8")
    return path

def main():
    interval = "1h"
    start = "2017-01-01"
    end = datetime.utcnow().strftime("%Y-%m-%d")
    r = requests.get(f"{BASE}/fapi/v1/exchangeInfo", timeout=30)
    r.raise_for_status()
    info = r.json()
    symbols = []
    for s in info.get("symbols", []):
        if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
            symbols.append(s["symbol"])
    for sym in symbols:
        try:
            df = collect(sym, interval, start, end)
            if df.empty:
                continue
            path = save_csv(df, interval, sym)
            print(path, len(df))
        except Exception as e:
            print(sym, "error", str(e))

if __name__ == "__main__":
    main()
