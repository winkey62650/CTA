import os
import time
import requests
from datetime import datetime
from joblib import Parallel, delayed
import pandas as pd
from cta_api.binance_fetcher import collect, save_csv
from config import root_path
import config as global_config

def usdt_perpetual_symbols():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=20, headers=headers)
        r.raise_for_status()
        info = r.json()
        syms = []
        for s in info.get("symbols", []):
            if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT":
                syms.append(s["symbol"])
        return syms
    except Exception as e:
        fallback = getattr(global_config, "symbol_list", [])
        print("fetch symbols error:", e)
        print("fallback to config.symbol_list:", fallback)
        return fallback


def _interval_delta(interval: str) -> pd.Timedelta:
    if interval.endswith("m"):
        return pd.to_timedelta(int(interval[:-1]), unit="m")
    if interval.endswith("h"):
        return pd.to_timedelta(int(interval[:-1]), unit="h")
    if interval.endswith("d"):
        return pd.to_timedelta(int(interval[:-1]), unit="d")
    raise ValueError(interval)


def _download_one(sym: str, interval: str, start: str, end: str):
    try:
        csv_dir = os.path.join(root_path, "data", "market_csv", interval.upper())
        os.makedirs(csv_dir, exist_ok=True)
        s = sym if "-" in sym else sym.replace("USDT", "-USDT")
        csv_path = os.path.join(csv_dir, f"{s}.csv")
        from_start = start
        base_df = None
        if os.path.exists(csv_path):
            try:
                base_df = pd.read_csv(csv_path, parse_dates=["candle_begin_time"])
                if base_df.empty:
                    base_df = None
                else:
                    base_df = base_df.dropna(subset=["candle_begin_time"])
                    base_df = base_df.drop_duplicates(subset=["candle_begin_time"])
                    base_df = base_df.sort_values("candle_begin_time")
                    times = base_df["candle_begin_time"].reset_index(drop=True)
                    delta = times.diff().dropna()
                    step = _interval_delta(interval)
                    if not delta.eq(step).all():
                        print(sym, "local csv not continuous, redownload from", start)
                        base_df = None
                    else:
                        last_ts = times.iloc[-1]
                        end_ts = pd.Timestamp(end) if end is not None else pd.Timestamp.utcnow()
                        if last_ts >= end_ts - step:
                            print(sym, "already up to date, last:", last_ts, "target:", end_ts)
                            return
                        from_start = (last_ts + step).strftime("%Y-%m-%d %H:%M:%S")
                        print(sym, "incremental from", from_start)
            except Exception as e:
                print(sym, "read local csv error, redownload from", start, e)
                base_df = None
        base_sleep = getattr(global_config, "data_fetch_no_data_sleep", 5.0)
        max_retries = getattr(global_config, "data_fetch_no_data_max_retries", 3)
        sleep_time = base_sleep
        attempt = 0
        while True:
            df = collect(sym, interval, from_start, end)
            if not df.empty:
                if base_df is not None:
                    all_df = pd.concat([base_df, df], ignore_index=True)
                    all_df = all_df.dropna(subset=["candle_begin_time"])
                    all_df = all_df.drop_duplicates(subset=["candle_begin_time"])
                    all_df = all_df.sort_values("candle_begin_time")
                else:
                    all_df = df
                all_df.to_csv(csv_path, index=False, encoding="utf-8")
                print(sym, "saved", csv_path, "shape", all_df.shape)
                return
            attempt += 1
            print(sym, "no data", f"(attempt {attempt}/{max_retries})")
            if attempt >= max_retries or sleep_time <= 0:
                print(sym, "no data after retries, skip")
                return
            print(sym, "sleep", sleep_time, "seconds before retry")
            time.sleep(sleep_time)
            sleep_time *= 2
    except Exception as e:
        print(sym, "error", str(e))


def run(interval="1h", start="2019-09-01", end=None, limit=None, workers: int = 4):
    end = end or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    syms = usdt_perpetual_symbols()
    if limit:
        syms = syms[:limit]
    symbol_delay = getattr(global_config, "data_fetch_symbol_delay", 0.0)
    if workers is None or workers <= 1:
        total = len(syms)
        for idx, sym in enumerate(syms, 1):
            progress = idx / total * 100 if total else 0
            print(f"[{idx}/{total}] {sym} ({progress:.1f}%)")
            _download_one(sym, interval, start, end)
            if symbol_delay > 0:
                time.sleep(symbol_delay)
    else:
        Parallel(n_jobs=workers)(
            delayed(_download_one)(sym, interval, start, end) for sym in syms
        )

if __name__ == "__main__":
    run(
        getattr(global_config, "data_fetch_interval", "1h"),
        getattr(global_config, "data_fetch_start", "2019-09-01"),
        getattr(global_config, "data_fetch_end", None),
        getattr(global_config, "data_fetch_limit", 5),
        getattr(global_config, "data_fetch_workers", 4),
    )
