import argparse
import os
import subprocess
from config import root_path
import scripts.prepare_feather_from_csv as conv
import cta_api.cta_core as core
import config as cfg

def ensure_pickle(symbol, interval):
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    pkl = os.path.join(root_path, "data", "pickle_data", interval.upper(), f"{s}.pkl")
    if not os.path.exists(pkl):
        conv.convert(symbol, interval)
    return pkl

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", required=True)
    ap.add_argument("--symbols", required=True, help="逗号分隔，如 BTC-USDT,ETH-USDT")
    ap.add_argument("--interval", default="1H")
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2026-01-01")
    ap.add_argument("--para", type=int, default=180)
    ap.add_argument("--proportion", type=float, default=0.5)
    ap.add_argument("--leverage", type=float, default=1.0)
    args = ap.parse_args()

    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    for s in syms:
        ensure_pickle(s, args.interval)

    cfg.signal_name_list = [args.factor]
    cfg.symbol_list = syms
    cfg.rule_type_list = [args.interval]
    cfg.date_start = args.start
    cfg.date_end = args.end
    cfg.para = [args.para]
    cfg.proportion = args.proportion
    cfg.leverage_rate = args.leverage

    multiple_process = False
    core.base_data(cfg.symbol_list, args.interval, multiple_process)
    core.stg_date(cfg.symbol_list, args.interval, multiple_process)

if __name__ == "__main__":
    main()

