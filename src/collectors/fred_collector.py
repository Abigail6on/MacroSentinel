import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

# Fix for potential SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

# 1. Load Environment
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# 2. Configuration
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
    macro_df = pd.DataFrame()

    # A. Fetch FRED Indicators
    for code, name in INDICATORS.items():
        print(f"   [FETCHING FRED] {name}...")
        try:
            series = fred.get_series(code)
            macro_df[name] = series
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")

    # B. Fetch Sector Rotation Signals (XLF vs XLU)
    print("   [FETCHING MARKET] XLF & XLU Sectors...")
    try:
        # Pull 30 days of hourly data for rotation analysis
        sectors = yf.download(["XLF", "XLU"], period="1mo", interval="1h")['Close']
        sectors.index = sectors.index.tz_localize(None)
        
        # Merge sector data into macro dataframe
        macro_df = macro_df.reindex(sectors.index).ffill()
        macro_df['XLF'] = sectors['XLF']
        macro_df['XLU'] = sectors['XLU']
    except Exception as e:
        print(f"   [ERROR] Failed to fetch Sector ETFs: {e}")

    # 3. Clean and Save
    macro_df = macro_df.ffill().dropna()
    
    # Path Management
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    output_path = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    macro_df.to_csv(output_path)
    print(f"[SUCCESS] Macro & Sector data saved to {output_path}")

if __name__ == "__main__":
    fetch_macro_data()