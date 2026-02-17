import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl
from datetime import datetime

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
    if not FRED_KEY: return
    print("--- Phase C Collector: Syncing 2026 Data ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL history to bridge the 2024-2026 gap
    macro_frames = []
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except: continue
    
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    # 2. Fetch Market Data (Added SPY for Phase C RSI)
    print("   [FETCHING] XLF, XLU, and SPY for Tactical RSI...")
    try:
        data = yf.download(["XLF", "XLU", "SPY"], period="1mo", interval="1h")
        sectors = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
        sectors.index = sectors.index.tz_localize(None)
        
        # Align macro data to hourly market time
        final_df = macro_df.reindex(sectors.index, method='ffill')
        for t in ["XLF", "XLU", "SPY"]:
            if t in sectors.columns: final_df[t] = sectors[t]
        
        # --- THE FIX: Look back 1 year from the CURRENT hour ---
        full_cpi = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [
            full_cpi.asof(t - pd.DateOffset(years=1)) for t in final_df.index
        ]

        # 3. Save to Root
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        final_df.to_csv(os.path.join(output_dir, "macro_indicators_raw.csv"))
        print(f"[SUCCESS] 2026 Data Bridge Active. Inflation anchor found.")
    except Exception as e:
        print(f"[ERROR] Collector failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()