import os
from joblib import Parallel, delayed
import pandas as pd
from config import root_path
import config as global_config

def convert(symbol: str, interval: str, skip_existing: bool = True):
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    src = os.path.join(root_path, "data", "market_csv", interval.upper(), f"{s}.csv")
    dst_dir = os.path.join(root_path, "data", "pickle_data", interval.upper())
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f"{s}.pkl")
    if skip_existing and os.path.exists(dst):
        print("skip existing:", dst)
        return
    df = pd.read_csv(src, parse_dates=["candle_begin_time"])
    df["offset"] = 0
    df["kline_pct"] = pd.to_numeric(df["close"], errors="coerce").pct_change().fillna(0.0)
    cols = [
        "candle_begin_time","open","high","low","close","volume","quote_volume","trade_num",
        "taker_buy_base_asset_volume","taker_buy_quote_asset_volume","taker_sell_quote_asset_volume",
        "offset","kline_pct"
    ]
    df = df[cols]
    try:
        print("sample head for", s, "interval", interval)
        print(df.head(5).to_string())
        print("dtypes:")
        print(df.dtypes)
    except Exception as e:
        print("print sample error:", symbol, e)
    df.to_feather(dst)
    print("saved:", dst, len(df))


def batch_convert(interval: str, workers: int = 4, skip_existing: bool = True):
    src_dir = os.path.join(root_path, "data", "market_csv", interval.upper())
    if not os.path.exists(src_dir):
        print("csv 目录不存在：", src_dir)
        return
    files = [f for f in os.listdir(src_dir) if f.endswith(".csv")]
    if not files:
        print("没有找到任何 csv 文件：", src_dir)
        return
    symbols = [f.replace(".csv", "") for f in files]
    def _run_one(s):
        sym = s if "-" in s else s.replace("-USDT", "USDT")
        try:
            convert(sym, interval, skip_existing=skip_existing)
        except Exception as e:
            print("convert error:", sym, e)
    if workers is None or workers <= 1:
        for s in symbols:
            _run_one(s)
    else:
        Parallel(n_jobs=workers)(delayed(_run_one)(s) for s in symbols)

if __name__ == "__main__":
    symbol = getattr(global_config, "data_convert_symbol", None)
    interval = getattr(global_config, "data_convert_interval", "1h")
    workers = getattr(global_config, "data_convert_workers", 4)
    skip_existing = getattr(global_config, "data_convert_skip_existing", True)
    if symbol:
        convert(symbol, interval, skip_existing=skip_existing)
    else:
        batch_convert(interval, workers=workers, skip_existing=skip_existing)
