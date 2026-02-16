import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv

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
    print("--- Phase B: Harvesting Macro & Sector Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL FRED history (ensures YoY math works)
    macro_frames = []
    for code, name in INDICATORS.items():
        series = fred.get_series(code)
        macro_frames.append(pd.DataFrame({name: series}))
    
    macro_df = pd.concat(macro_frames, axis=1).ffill()

    # 2. Fetch Recent Market Data
    sectors = yf.download(["XLF", "XLU"], period="1mo", interval="1h")['Close']
    sectors.index = sectors.index.tz_localize(None)
    
    # 3. Join them: We keep all Macro rows that have sector data
    # This "inner" join ensures we only calculate for the active session
    final_df = macro_df.reindex(sectors.index, method='ffill')
    final_df['XLF'] = sectors['XLF']
    final_df['XLU'] = sectors['XLU']
    
    # BACKFILL Inflation only for the YoY calculation
    # We grab the CPI value from exactly 1 year ago to fill the gap
    full_cpi = fred.get_series('CPIAUCSL')
    final_df['Inflation_CPI_LastYear'] = [full_cpi.asof(t - pd.DateOffset(years=1)) for t in final_df.index]

    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "macro_indicators_raw.csv")
    final_df.to_csv(output_path)
    print(f"[SUCCESS] Data saved with YoY historical support.")

if __name__ == "__main__":
    fetch_macro_data()