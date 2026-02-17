import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

# Fix for SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# Configuration: slow macro facts
INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate',
    'VIXCLS': 'VIX_Index'
}

def fetch_macro_data():
    if not FRED_KEY:
        print("[ERROR] No FRED_API_KEY found!")
        return

    print("--- Phase B & C: Harvesting Macro, Sector, and Price Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL FRED history to support YoY calculations
    macro_frames = []
    for code, name in INDICATORS.items():
        print(f"   [FETCHING FRED] {name}...")
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")
    
    # Standardize macro dataframe
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    # 2. Fetch Recent Market Data (Added SPY for Phase C RSI)
    print("   [FETCHING MARKET] XLF, XLU, and SPY...")
    try:
        # Fetching 1 month of hourly data
        data = yf.download(["XLF", "XLU", "SPY"], period="1mo", interval="1h")
        
        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            sectors = data['Close']
        else:
            sectors = data
            
        sectors.index = sectors.index.tz_localize(None)
        
        # Align macro data to the hourly market index
        final_df = macro_df.reindex(sectors.index, method='ffill')
        
        # Safely assign market columns
        for ticker in ["XLF", "XLU", "SPY"]:
            if ticker in sectors.columns:
                final_df[ticker] = sectors[ticker]
        
        # --- THE INFLATION BRIDGE FIX ---
        # Look up the CPI value from exactly 1 year ago for every hourly timestamp
        full_cpi_series = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [
            full_cpi_series.asof(t - pd.DateOffset(years=1)) for t in final_df.index
        ]

        # 3. Save to Project Root
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "macro_indicators_raw.csv")
        final_df.to_csv(output_path)
        print(f"[SUCCESS] Data saved with 1-year Inflation Bridge and SPY data.")

    except Exception as e:
        print(f"   [ERROR] Market data processing failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()