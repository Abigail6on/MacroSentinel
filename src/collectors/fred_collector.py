import os
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

# --- UPDATED INDICATORS ---
# Added M2SL for Liquidity tracking
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
        print("[ERROR] FRED API Key missing.")
        return
        
    print("--- Phase C: Harvesting Macro & Liquidity Data ---")
    fred = Fred(api_key=FRED_KEY)
    
    macro_frames = []
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"[ERROR] Could not fetch {code}: {e}")
            continue
    
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    try:
        # 1. Download Market Data
        data = yf.download(TICKERS, period="1mo", interval="1h")
        market_data = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
        market_data.index = market_data.index.tz_localize(None)
        
        # 2. Align Macro to the Hourly Market Grid
        final_df = macro_df.reindex(market_data.index, method='ffill')
        
        # 3. Add Market Tickers
        for t in TICKERS:
            if t in market_data.columns:
                final_df[t] = market_data[t]
        
        # 4. Create Historical Bridges (For YoY Calculations)
        # We need the values from exactly 1 year ago to calculate growth
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
        
        print(f"[SUCCESS] Updated raw data with {final_df.columns.tolist()}")
        
    except Exception as e:
        print(f"[ERROR] Collector failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()