import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 1. Load Environment
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# 2. Configuration: The "Macro Watchlist"
# CPI = Inflation, T10Y2Y = Yield Curve, FEDFUNDS = Interest Rates, UNRATE = Unemployment
INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate'
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
            # Fetch latest 5 years of data
            series = fred.get_series(code)
            macro_df[name] = series
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")

    # 3. Clean and Save
    # Forward fill missing values (economic data is often monthly/quarterly)
    macro_df = macro_df.ffill().dropna()
    
    # Save to Raw data folder
    output_path = "../../data/raw/macro_indicators_raw.csv"
    
    # Ensure directory exists (helper for relative path execution)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    macro_df.to_csv(output_path)
    print(f"\n✅ SUCCESS: Macro data saved to {output_path}")
    print(f"📊 Dataset Shape: {macro_df.shape}")

if __name__ == "__main__":
    fetch_macro_data()