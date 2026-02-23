import os
import sys
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# Tickers needed for the Strategy Map
TICKERS = ["SPY", "QQQ", "GLD", "SHY", "XLF", "XLU"]

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
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"[ERROR] Could not fetch FRED indicator {code}: {e}")
            continue
            
    if not macro_frames:
        print("[ERROR] All FRED indicator fetches failed.")
        sys.exit(1)
        
    # We use sort=False to silence the warning, but then explicitly sort the index chronologically
    macro_df = pd.concat(macro_frames, axis=1, sort=False)
    macro_df = macro_df.sort_index()  # <--- THE FIX
    macro_df = macro_df[~macro_df.index.duplicated(keep='first')] # Drop bizarre duplicates
    
    # 1. Fetch Market Data 
    print("Downloading market data...")
    try:
        market_data = yf.download(TICKERS, period="1mo", interval="1h")
        
        if market_data.empty:
            print("[ERROR] Failed to fetch market data from Yahoo Finance.")
            sys.exit(1)
            
        market_data = market_data['Close'] if isinstance(market_data.columns, pd.MultiIndex) else market_data
        market_data.index = market_data.index.tz_localize(None)
        
        # Bulletproof the market data index as well
        market_data = market_data.sort_index()
        market_data = market_data[~market_data.index.duplicated(keep='first')]
        
    except Exception as e:
        print(f"[ERROR] Yahoo Finance Download Crashed: {e}")
        sys.exit(1)
        
    # 2. Align Macro to the Hourly Market Grid (Requires Monotonic Index)
    final_df = macro_df.reindex(market_data.index, method='ffill')
    
    # 3. Add Market Tickers
    for t in TICKERS:
        if t in market_data.columns:
            final_df[t] = market_data[t]
    
    # 4. Create Historical Bridges (For YoY Calculations)
    for base_col, year_ago_col in [('Inflation_CPI', 'Inflation_CPI_LastYear'), 
                                   ('Liquidity_M2', 'Liquidity_M2_LastYear')]:
        if base_col in macro_df.columns:
            full_series = macro_df[base_col]
            final_df[year_ago_col] = [
                full_series.asof(t - pd.DateOffset(years=1)) for t in final_df.index
            ]

    # 5. Save Output
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(ROOT_DIR, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "macro_indicators_raw.csv")
    final_df.to_csv(output_path)
    
    columns_updated = ['Inflation_CPI', 'Yield_Curve_10Y2Y', 'Fed_Funds_Rate', 'Unemployment_Rate', 'VIX_Index', 'Liquidity_M2', 'SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'Inflation_CPI_LastYear', 'Liquidity_M2_LastYear']
    print(f"[SUCCESS] Updated raw data with {columns_updated}")

def main():
    try:
        fetch_macro_data()
    except Exception as e:
        print(f"[FATAL ERROR] Collector failed completely: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()