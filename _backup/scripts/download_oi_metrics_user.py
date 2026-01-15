import requests
import pandas as pd
import zipfile
import io
import os
from datetime import datetime

SYMBOL = 'BTCUSDT'
START_YEAR = 2021
END_YEAR = 2024
SAVE_DIR = './data_oi_fixed'

def download_binance_metrics(symbol, start_year, end_year, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    all_dfs = []
    base_url = "https://data.binance.vision/data/futures/um/monthly/metrics"
    print(f"开始通过 Metrics 下载 {symbol} 历史持仓数据 ({start_year}-{end_year})...")
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            month_str = f"{month:02d}"
            if year == datetime.now().year and month >= datetime.now().month:
                break
            file_name = f"{symbol}-metrics-{year}-{month_str}"
            download_url = f"{base_url}/{symbol}/{file_name}.zip"
            try:
                print(f"正在下载: {year}-{month_str} (Metrics包) ...", end="")
                response = requests.get(download_url, stream=True, timeout=30)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_name = f"{file_name}.csv"
                        with z.open(csv_name) as f:
                            df = pd.read_csv(f)
                            cols = df.columns.tolist()
                            if 'create_time' in cols:
                                time_col = 'create_time'
                            elif 'time' in cols:
                                time_col = 'time'
                            elif 'timestamp' in cols:
                                time_col = 'timestamp'
                            else:
                                time_col = None
                            oi_col = 'sum_open_interest' if 'sum_open_interest' in cols else ('openInterest' if 'openInterest' in cols else None)
                            oiv_col = 'sum_open_interest_value' if 'sum_open_interest_value' in cols else ('openInterestValue' if 'openInterestValue' in cols else None)
                            if time_col is None or oi_col is None:
                                print(" 列缺失")
                                continue
                            target_df = df[[time_col, oi_col] + ([oiv_col] if oiv_col else [])].copy()
                            target_df.rename(columns={time_col:'datetime', oi_col:'openInterest', (oiv_col if oiv_col else oi_col):'openInterestValue'}, inplace=True)
                            try:
                                if pd.api.types.is_integer_dtype(target_df['datetime']) or pd.api.types.is_float_dtype(target_df['datetime']):
                                    target_df['datetime'] = pd.to_datetime(target_df['datetime'], unit='ms', errors='coerce')
                                else:
                                    target_df['datetime'] = pd.to_datetime(target_df['datetime'], errors='coerce')
                            except Exception:
                                target_df['datetime'] = pd.to_datetime(target_df['datetime'], errors='coerce')
                            all_dfs.append(target_df)
                    print(" 成功")
                elif response.status_code == 404:
                    print(" 无数据")
                else:
                    print(f" 错误 {response.status_code}")
            except Exception as e:
                print(f" 异常: {e}")
    if all_dfs:
        print("正在合并清洗...")
        full_df = pd.concat(all_dfs, ignore_index=True)
        full_df = full_df.sort_values('datetime')
        output_path = os.path.join(save_dir, f"{symbol}_OI_History_Fixed.csv")
        full_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"成功！数据已保存至: {output_path}")
        print(f"时间范围: {full_df['datetime'].min()} 至 {full_df['datetime'].max()}")
        print(f"数据总条数: {len(full_df)}")
        print(full_df.head(3))
    else:
        print("未获取到任何数据。")

if __name__ == "__main__":
    download_binance_metrics(SYMBOL, START_YEAR, END_YEAR, SAVE_DIR)

