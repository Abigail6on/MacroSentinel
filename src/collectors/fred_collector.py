import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# Tickers needed for the Strategy Map in performance_engine
TICKERS = ["SPY", "QQQ", "GLD", "SHY", "XLF", "XLU"]

INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate',
    'VIXCLS': 'VIX_Index'
}

def fetch_macro_data():
    if not FRED_KEY: return
    print("--- Phase C: Harvesting Macro & All Market Tickers ---")
    fred = Fred(api_key=FRED_KEY)
    
    macro_frames = []
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except: continue
    
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    try:
        # 1. Download ALL required tickers
        data = yf.download(TICKERS, period="1mo", interval="1h")
        market_data = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
        market_data.index = market_data.index.tz_localize(None)
        
        # 2. Align Macro to the Hourly Market Grid
        final_df = macro_df.reindex(market_data.index, method='ffill')
        
        # 3. Explicitly add all tickers to the CSV
        for t in TICKERS:
            if t in market_data.columns:
                final_df[t] = market_data[t]
        
        # 4. Create Inflation Bridge
        full_cpi = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [
            full_cpi.asof(t - pd.DateOffset(years=1)) for t in final_df.index
        ]

        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        final_df.to_csv(os.path.join(output_dir, "macro_indicators_raw.csv"))
        print(f"[SUCCESS] Saved hourly data with {final_df.columns.tolist()}")
    except Exception as e:
        print(f"[ERROR] Collector failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()