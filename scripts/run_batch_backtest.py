import argparse
import os
import pandas as pd
from datetime import datetime
from config import root_path
import config as cfg
import scripts.prepare_feather_from_csv as conv
from importlib import import_module

def ensure_pickle(symbol, interval):
    s = symbol if "-" in symbol else symbol.replace("USDT","-USDT")
    pkl = os.path.join(root_path, "data", "pickle_data", interval.upper(), f"{s}.pkl")
    if not os.path.exists(pkl):
        conv.convert(symbol, interval)
    return pkl

def gen_para_list(pstr):
    if "," in pstr:
        parts = [x.strip() for x in pstr.split(",") if x.strip()]
        return [int(x) for x in parts]
    if ":" in pstr:
        a,b,c = [int(x) for x in pstr.split(":")]
        return list(range(a,b+1,c))
    return [int(pstr)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", required=True)
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--interval", default="1H")
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--end", default="2026-01-01")
    ap.add_argument("--para", required=True, help="如 '10:200:10' 或 '5,10,15'")
    args = ap.parse_args()

    factor = args.factor
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    para_list = gen_para_list(args.para)

    cfg.signal_name_list = [factor]
    cfg.rule_type_list = [args.interval]
    cfg.date_start = args.start
    cfg.date_end = args.end

    for symbol in syms:
        ensure_pickle(symbol, args.interval)
        df = pd.read_feather(os.path.join(root_path, "data", "pickle_data", args.interval.upper(), f"{symbol}.pkl"))
        min_amount = cfg.min_amount_dict[symbol]
        mod = import_module("3_fastover")
        calc = getattr(mod, "calculate_by_one_loop")
        results = []
        for para in para_list:
            r = calc(para=para, df=df, signal_name=factor, symbol=symbol, rule_type=args.interval, min_amount=min_amount, start=args.start, end=args.end)
            if r is not None and not r.empty:
                r["para"] = str(para)
                results.append(r)
        if results:
            out = pd.concat(results, ignore_index=True)
            out_path = os.path.join(root_path, "data", "output", "para", f"{factor}&{symbol}&{cfg.leverage_rate}&{args.interval}.csv")
            if os.path.exists(out_path):
                out.to_csv(out_path, index=False, header=False, mode="a", encoding="gbk")
            else:
                out.to_csv(out_path, index=False, encoding="gbk")
            print("saved:", out_path, len(out))

if __name__ == "__main__":
    main()
