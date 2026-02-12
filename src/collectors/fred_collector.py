import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv
import ssl

# Fix for potential SSL certificate issues on some macOS environments
ssl._create_default_https_context = ssl._create_unverified_context

# 1. Load Environment
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# 2. Configuration: The "Macro Watchlist"
# Added VIXCLS (CBOE Volatility Index) to provide a "Fear Filter"
INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate',
    'VIXCLS': 'VIX_Index'
}

def fetch_macro_data():
    if not FRED_KEY:
        print("[ERROR] No FRED_API_KEY found in .env file!")
        return

    print("Initializing MacroSentinel FRED Collector...")
    fred = Fred(api_key=FRED_KEY)
    
    macro_df = pd.DataFrame()

    for code, name in INDICATORS.items():
        print(f"   [FETCHING] {name} ({code})...")
        try:
            # Fetch latest data
            series = fred.get_series(code)
            macro_df[name] = series
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")

    # 3. Clean and Save
    # Forward fill missing values (macro data is monthly, VIX is daily)
    macro_df = macro_df.ffill().dropna()
    
    # Path Management
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
    output_path = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    macro_df.to_csv(output_path)
    print(f"[SUCCESS] Macro data (including VIX) saved to {output_path}")

if __name__ == "__main__":
    fetch_macro_data()