import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

# Fix for SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

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

    print("--- Phase B: Harvesting Macro & Sector Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL FRED history
    macro_frames = []
    for code, name in INDICATORS.items():
        print(f"   [FETCHING FRED] {name}...")
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")
    
    # Use sort=False to silence the Pandas4Warning
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    # 2. Fetch Recent Market Data
    print("   [FETCHING MARKET] XLF & XLU Sectors...")
    try:
        sectors = yf.download(["XLF", "XLU"], period="1mo", interval="1h")['Close']
        sectors.index = sectors.index.tz_localize(None)
        
        # Join market data with macro data
        final_df = macro_df.reindex(sectors.index, method='ffill')
        final_df['XLF'] = sectors['XLF']
        final_df['XLU'] = sectors['XLU']
        
        # Calculate historical CPI bridge
        full_cpi = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [full_cpi.asof(t - pd.DateOffset(years=1)) for t in final_df.index]

        # --- CORRECTED PATH LOGIC ---
        # Moving up 3 levels: collectors -> src -> root
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        output_path = os.path.join(output_dir, "macro_indicators_raw.csv")
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        final_df.to_csv(output_path)
        print(f"[SUCCESS] Data saved to {output_path}")

    except Exception as e:
        print(f"   [ERROR] Market data processing failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()