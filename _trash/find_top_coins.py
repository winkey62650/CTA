import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

def find_top_coins():
    print("Initializing Binance Futures connection...")
    exchange = ccxt.binanceusdm()
    
    print("Loading markets...")
    markets = exchange.load_markets()
    
    print("Fetching 24h ticker data...")
    tickers = exchange.fetch_tickers()
    
    # Filter for USDT pairs and valid futures
    futures_tickers = []
    for symbol, ticker in tickers.items():
        if '/USDT' in symbol and ':USDT' in symbol: # Standard ccxt format for linear futures is usually BTC/USDT:USDT
            # Ensure it is a valid market
            if symbol in markets and markets[symbol]['active']:
                futures_tickers.append({
                    'symbol': symbol,
                    'volume': ticker['quoteVolume'] if ticker['quoteVolume'] else 0
                })
    
    # Sort by volume descending
    df = pd.DataFrame(futures_tickers)
    df = df.sort_values(by='volume', ascending=False)
    
    print(f"Found {len(df)} active USDT futures pairs.")
    print("Checking listing age for top volume coins (target: 30 coins > 2 years)...")
    
    qualified_coins = []
    checked_count = 0
    
    # Iterate through sorted list
    for index, row in df.iterrows():
        symbol = row['symbol']
        volume = row['volume']
        
        # Skip if we already have 30
        if len(qualified_coins) >= 30:
            break
            
        try:
            # Check listing date by fetching the first monthly kline
            # We need to look back far enough. 2 years ago from now.
            two_years_ago = datetime.now() - timedelta(days=365*2)
            two_years_ago_ts = int(two_years_ago.timestamp() * 1000)
            
            # Fetch earliest candle available
            # binance usually allows fetching from specific start time. 
            # If we ask for a candle from 2018, and it returns one from 2020, then it was listed in 2020.
            # But easier: fetch OHLCV with limit=1, params={'startTime': 0} to get the very first candle
            # Note: start_time=0 might not work on all endpoints, but usually works for binance to get the first history.
            
            # Alternative: Fetch 1M timeframe, since=0, limit=1
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1M', since=0, limit=1)
            
            if ohlcv:
                first_ts = ohlcv[0][0]
                listing_date = datetime.fromtimestamp(first_ts / 1000)
                
                age_days = (datetime.now() - listing_date).days
                
                if listing_date < two_years_ago:
                    # Reformatted symbol for user (remove :USDT if present for readability, but keep unique)
                    # CCXT symbol: BTC/USDT:USDT -> User usually wants BTC-USDT
                    clean_symbol = symbol.split(':')[0].replace('/', '-')
                    
                    qualified_coins.append({
                        'symbol': clean_symbol,
                        'volume_24h': volume,
                        'listing_date': listing_date.strftime('%Y-%m-%d'),
                        'age_days': age_days
                    })
                    print(f"[MATCH] {clean_symbol}: Listed {listing_date.strftime('%Y-%m-%d')} ({age_days} days) - Vol: {volume:,.0f}")
                else:
                    print(f"[SKIP] {symbol}: Listed {listing_date.strftime('%Y-%m-%d')} ({age_days} days) - Too new")
            
            # Rate limit respect
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error checking {symbol}: {e}")
            
        checked_count += 1
        # Safety break to avoid infinite loop if something is wrong
        if checked_count > 200:
            print("Checked top 200 coins, stopping search.")
            break

    print("\n" + "="*50)
    print(f"Top {len(qualified_coins)} Coins (Volume Top 30 & Age > 2 Years)")
    print("="*50)
    
    # Create DataFrame for nice output
    res_df = pd.DataFrame(qualified_coins)
    if not res_df.empty:
        # Format volume
        res_df['volume_formatted'] = res_df['volume_24h'].apply(lambda x: f"${x:,.0f}")
        print(res_df[['symbol', 'listing_date', 'age_days', 'volume_formatted']].to_string(index=False))
        
        # Also save to csv
        res_df.to_csv('top_30_coins.csv', index=False)
        print("\nSaved to top_30_coins.csv")
        
        # Output list string for easy copy
        print("\nSymbol List (Comma separated):")
        print(",".join(res_df['symbol'].tolist()))
    else:
        print("No coins found matching criteria.")

if __name__ == "__main__":
    find_top_coins()
