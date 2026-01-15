import argparse
from datetime import datetime
from cta_api.binance_fetcher import collect, save_csv

def main():
    p = argparse.ArgumentParser()
    p.add_argument("symbol", help="如 BTCUSDT 或 BTC-USDT")
    p.add_argument("--interval", default="1h", help="周期，如 1h/4h/1d")
    p.add_argument("--start", default="2019-09-01", help="开始时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    p.add_argument("--end", default=datetime.utcnow().strftime("%Y-%m-%d"), help="结束时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    args = p.parse_args()

    df = collect(args.symbol, args.interval, args.start, args.end)
    if df.empty:
        print("no data")
        return
    path = save_csv(df, args.interval, args.symbol)
    print("saved:", path, "rows:", len(df))

if __name__ == "__main__":
    main()

