import os
import sys
import time
import random
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

TICKERS = ["SPY", "QQQ", "GLD", "SHY", "XLF", "XLU", "XLE", "TLT", "DBC", "EFA", "EEM"]

INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate',
    'VIXCLS': 'VIX_Index',
    'M2SL': 'Liquidity_M2' 
}

def fetch_macro_data():
    if not FRED_KEY: 
        print("[ERROR] FRED API Key missing in environment.")
        sys.exit(1)
        
    print("--- Phase C: Harvesting Macro & Liquidity Data ---")
    fred = Fred(api_key=FRED_KEY)
    macro_frames = []
    
    # 1. Robust FRED Fetching
    for code, name in INDICATORS.items():
        success = False
        for attempt in range(3):
            try:
                series = fred.get_series(code)
                macro_frames.append(pd.DataFrame({name: series}))
                success = True
                break
            except Exception as e:
                print(f"[WARNING] Attempt {attempt + 1} failed for FRED {code}: {e}")
                time.sleep(2)
        
        if not success:
            print(f"[ERROR] Completely failed to fetch FRED {code}. Creating empty placeholder.")
            # VULNERABILITY FIX: Append an empty column of NaNs instead of skipping
            macro_frames.append(pd.DataFrame(columns=[name], dtype=float))
            continue
            
    if not macro_frames:
        print("[ERROR] Failed to fetch any macro data.")
        sys.exit(1)
        
    macro_df = pd.concat(macro_frames, axis=1)
    macro_df.index = pd.to_datetime(macro_df.index)
    if macro_df.index.tz is not None:
        macro_df.index = macro_df.index.tz_localize(None)

    # 2. Native Yahoo Fetching via Ticker Object
    print("[INFO] Downloading market data using Ticker Objects to bypass IP filters...")
    
    price_series = {}
    for ticker in TICKERS:
        for attempt in range(3):
            try:
                stock = yf.Ticker(ticker)
                temp_df = stock.history(period="1mo", interval="1h")
                
                if not temp_df.empty and 'Close' in temp_df.columns:
                    clean_series = temp_df['Close'].squeeze()
                    if clean_series.index.tz is not None:
                        clean_series.index = clean_series.index.tz_localize(None)
                    
                    price_series[ticker] = clean_series
                    break
            except Exception as e:
                print(f"[WARNING] Attempt {attempt+1} failed for {ticker}: {e}")
            
            time.sleep(random.uniform(3.0, 5.0)) 
            
    if not price_series:
        print("[ERROR] Failed to fetch any market data from Yahoo Finance.")
        sys.exit(1)

    market_data = pd.DataFrame(price_series)

    # Align Macro Data to Hourly Market Grid
    final_df = macro_df.reindex(market_data.index, method='ffill')
    
    for t in TICKERS:
        if t in market_data.columns:
            final_df[t] = market_data[t]
    
    for base_col, year_ago_col in [('Inflation_CPI', 'Inflation_CPI_LastYear'), 
                                   ('Liquidity_M2', 'Liquidity_M2_LastYear')]:
        if base_col in macro_df.columns:
            full_series = macro_df[base_col]
            final_df[year_ago_col] = [
                full_series.asof(t - pd.DateOffset(years=1)) for t in final_df.index
            ]

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(ROOT_DIR, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "macro_indicators_raw.csv")
    final_df.to_csv(output_path)
    print(f"[SUCCESS] Macro dataset compiled with {len(final_df)} hourly records.")

if __name__ == "__main__":
    fetch_macro_data()