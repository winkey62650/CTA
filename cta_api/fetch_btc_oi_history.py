import os
import pandas as pd
from datetime import datetime
from cta_api.binance_vision_fetcher import _fetch_zip_csv
from config import root_path

BASE_M = "https://data.binance.vision/data/futures/um/monthly/openInterest"

def month_range(start_month: str, end_month: str) -> list[str]:
    s = pd.Period(start_month, freq="M")
    e = pd.Period(end_month, freq="M")
    months = []
    p = s
    while p <= e:
        months.append(p.strftime("%Y-%m"))
        p = (p.to_timestamp() + pd.offsets.MonthBegin(1)).to_period("M")
    return months

def fetch_btcusdt_oi_1h(start_month: str, end_month: str) -> pd.DataFrame:
    symbol = "BTCUSDT"
    period = "1h"
    rows = []
    for y_m in month_range(start_month, end_month):
        url = f"{BASE_M}/{symbol}/{period}/{symbol}-openInterest-{period}-{y_m}.zip"
        csv = f"{symbol}-openInterest-{period}-{y_m}.csv"
        df = _fetch_zip_csv(url, csv)
        if df.empty:
            continue
        rows.append(df)
        print("fetched", y_m, len(df))
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)
    ts_col = "timestamp" if "timestamp" in df.columns else ("time" if "time" in df.columns else None)
    if ts_col is None:
        return pd.DataFrame()
    df["candle_begin_time"] = pd.to_datetime(df[ts_col], unit="ms", errors="coerce")
    oi_col = "sumOpenInterest" if "sumOpenInterest" in df.columns else ("openInterest" if "openInterest" in df.columns else None)
    if oi_col is None:
        df["open_interest"] = pd.NA
    else:
        df["open_interest"] = pd.to_numeric(df[oi_col], errors="coerce")
    return df[["candle_begin_time", "open_interest"]]

def save_oi_csv(df: pd.DataFrame, interval: str = "1h") -> str:
    out_dir = os.path.join(root_path, "data", "oi_history", interval.upper())
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "BTC-USDT_oi.csv")
    df.to_csv(path, index=False, encoding="utf-8")
    return path

if __name__ == "__main__":
    end_month = datetime.utcnow().strftime("%Y-%m")
    df = fetch_btcusdt_oi_1h("2019-09", end_month)
    if df.empty:
        print("no data fetched from monthly archives")
    else:
        p = save_oi_csv(df, "1h")
        print("saved:", p, "rows:", len(df))

