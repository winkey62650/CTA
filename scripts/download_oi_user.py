import requests
import pandas as pd
import zipfile
import io
import os
from datetime import datetime

SYMBOL = 'BTCUSDT'
START_YEAR = 2021
END_YEAR = 2024
SAVE_DIR = './data_oi'

def download_and_merge_oi(symbol, start_year, end_year, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    all_dfs = []
    base_url = "https://data.binance.vision/data/futures/um/monthly/openInterest"
    print(f"开始下载 {symbol} 持仓量数据 ({start_year}-{end_year})...")

    for year in range(start_year, end_year + 1):
        for month in range(1, 12 + 1):
            month_str = f"{month:02d}"
            if year == datetime.now().year and month >= datetime.now().month:
                break
            file_name = f"{symbol}-openInterest-{year}-{month_str}"
            download_url = f"{base_url}/{symbol}/{file_name}.zip"
            try:
                print(f"尝试下载: {year}-{month_str} ...", end="")
                response = requests.get(download_url, stream=True, timeout=30)
                if response.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_name = f"{file_name}.csv"
                        with z.open(csv_name) as f:
                            df = pd.read_csv(f)
                            if df.shape[1] == 4:
                                df.columns = ['symbol', 'timestamp', 'openInterest', 'openInterestValue']
                            elif 'timestamp' in df.columns:
                                if 'sumOpenInterest' in df.columns:
                                    df.rename(columns={'sumOpenInterest':'openInterest','sumOpenInterestValue':'openInterestValue'}, inplace=True)
                                elif 'openInterest' in df.columns and 'openInterestValue' not in df.columns:
                                    df['openInterestValue'] = None
                            all_dfs.append(df)
                    print(" 成功")
                elif response.status_code == 404:
                    print(" 无数据")
                else:
                    print(f" 错误 {response.status_code}")
            except Exception as e:
                print(f" 异常: {e}")

    if all_dfs:
        print("合并数据...")
        full_df = pd.concat(all_dfs, ignore_index=True)
        if 'timestamp' in full_df.columns:
            full_df['datetime'] = pd.to_datetime(full_df['timestamp'], unit='ms', errors='coerce')
        elif 'time' in full_df.columns:
            full_df['datetime'] = pd.to_datetime(full_df['time'], unit='ms', errors='coerce')
        else:
            full_df['datetime'] = pd.NaT
        full_df = full_df.sort_values('datetime')
        final_df = full_df[['datetime', 'openInterest', 'openInterestValue']].copy()
        output_path = os.path.join(save_dir, f"{symbol}_OI_History.csv")
        final_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"已保存至: {output_path}")
        print(f"共获取 {len(final_df)} 条数据")
        print(final_df.head())
        print(final_df.tail())
    else:
        print("没有下载到任何数据，请检查年份或网络。")

if __name__ == "__main__":
    download_and_merge_oi(SYMBOL, START_YEAR, END_YEAR, SAVE_DIR)

