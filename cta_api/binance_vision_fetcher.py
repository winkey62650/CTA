import io
import zipfile
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

BASE = "https://data.binance.vision/data/futures/um/daily"
BASE_M = "https://data.binance.vision/data/futures/um/monthly"

def _date_iter(start: str, end: str):
    s = pd.Timestamp(start).normalize()
    e = pd.Timestamp(end).normalize()
    d = s
    while d <= e:
        yield d.strftime("%Y-%m-%d")
        d += pd.Timedelta(days=1)

def _fetch_zip_csv(url: str, csv_name: str) -> pd.DataFrame:
    h = requests.head(url, timeout=20)
    if h.status_code != 200:
        return pd.DataFrame()
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    name = csv_name if csv_name in names else names[0]
    with z.open(name) as f:
        df = pd.read_csv(f)
    return df

def _list_files(prefix: str, pattern: str) -> list[str]:
    url = f"https://data.binance.vision/?prefix={requests.utils.quote(prefix, safe='')}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return []
    text = r.text
    regex = re.compile(r'href="([^"]+)"')
    files = []
    for m in regex.finditer(text):
        href = m.group(1)
        if href.endswith(".zip") and re.search(pattern, href):
            if not href.startswith("http"):
                href = "https://data.binance.vision" + ("/" + href.lstrip("/"))
            files.append(href)
    return files

def fetch_oi(symbol: str, period: str, start: str, end: str) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    rows = []
    monthly_prefix = f"data/futures/um/monthly/openInterest/{sym}/{period}/"
    pattern_month = rf"{sym}-openInterest-{period}-\d{{4}}-\d{{2}}\.zip"
    files = _list_files(monthly_prefix, pattern_month)
    for f in files:
        csv = f.split("/")[-1].replace(".zip", ".csv")
        df = _fetch_zip_csv(f, csv)
        if not df.empty:
            rows.append(df)
    if not rows:
        daily_prefix = f"data/futures/um/daily/openInterest/{sym}/"
        pattern_daily = rf"{sym}-openInterest-{period}-\d{{4}}-\d{{2}}-\d{{2}}\.zip"
        files = _list_files(daily_prefix, pattern_daily)
        for f in files:
            csv = f.split("/")[-1].replace(".zip", ".csv")
            df = _fetch_zip_csv(f, csv)
            if not df.empty:
                rows.append(df)
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)
    ts = df["timestamp"] if "timestamp" in df.columns else df["time"]
    df["candle_begin_time"] = pd.to_datetime(ts, unit="ms", errors="coerce")
    if "sumOpenInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["sumOpenInterest"], errors="coerce")
    elif "openInterest" in df.columns:
        df["open_interest"] = pd.to_numeric(df["openInterest"], errors="coerce")
    else:
        df["open_interest"] = np.nan
    return df[["candle_begin_time","open_interest"]]

def fetch_funding(symbol: str, start: str, end: str) -> pd.DataFrame:
    sym = symbol.replace("-", "")
    rows = []
    daily_prefix = f"data/futures/um/daily/fundingRate/{sym}/"
    pattern_daily = rf"{sym}-fundingRate-\d{{4}}-\d{{2}}-\d{{2}}\.zip"
    daily_files = _list_files(daily_prefix, pattern_daily)
    for f in daily_files:
        csv = f.split("/")[-1].replace(".zip", ".csv")
        df = _fetch_zip_csv(f, csv)
        if not df.empty:
            rows.append(df)
    if not rows:
        s = pd.Timestamp(start).normalize().to_period("M")
        e = pd.Timestamp(end).normalize().to_period("M")
        p = s
        while p <= e:
            y_m = p.strftime("%Y-%m")
            monthly_prefix = f"data/futures/um/monthly/fundingRate/{sym}/"
            pattern_month = rf"{sym}-fundingRate-{y_m}\.zip"
            files = _list_files(monthly_prefix, pattern_month)
            for f in files:
                csv = f.split("/")[-1].replace(".zip", ".csv")
                df = _fetch_zip_csv(f, csv)
                if not df.empty:
                    rows.append(df)
            p = (p.to_timestamp() + pd.offsets.MonthBegin(1)).to_period("M")
    if not rows:
        return pd.DataFrame()
    df = pd.concat(rows, ignore_index=True)
    col = "fundingTime" if "fundingTime" in df.columns else ("time" if "time" in df.columns else ("timestamp" if "timestamp" in df.columns else None))
    if col is None:
        return pd.DataFrame()
    df["funding_time"] = pd.to_datetime(df[col], unit="ms", errors="coerce")
    frcol = "fundingRate" if "fundingRate" in df.columns else ("rate" if "rate" in df.columns else ("funding_rate" if "funding_rate" in df.columns else None))
    if frcol is None:
        df["funding_rate"] = np.nan
    else:
        df["funding_rate"] = pd.to_numeric(df[frcol], errors="coerce")
    return df[["funding_time","funding_rate"]]
