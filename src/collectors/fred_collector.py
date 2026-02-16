import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

INDICATORS = {'CPIAUCSL': 'Inflation_CPI', 'T10Y2Y': 'Yield_Curve_10Y2Y', 
              'FEDFUNDS': 'Fed_Funds_Rate', 'UNRATE': 'Unemployment_Rate', 'VIXCLS': 'VIX_Index'}

def fetch_macro_data():
    if not FRED_KEY: return
    print("--- Phase B: Harvesting Macro & Sector Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    macro_frames = []
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except: continue
    
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    print("   [FETCHING MARKET] XLF & XLU Sectors...")
    try:
        # Download and specifically extract the 'Close' prices
        data = yf.download(["XLF", "XLU"], period="1mo", interval="1h")
        
        # Handle potential multi-index column issues
        if isinstance(data.columns, pd.MultiIndex):
            sectors = data['Close']
        else:
            sectors = data
            
        sectors.index = sectors.index.tz_localize(None)
        
        final_df = macro_df.reindex(sectors.index, method='ffill')
        
        # Safely assign columns
        if 'XLF' in sectors.columns: final_df['XLF'] = sectors['XLF']
        if 'XLU' in sectors.columns: final_df['XLU'] = sectors['XLU']
        
        full_cpi = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [full_cpi.asof(t - pd.DateOffset(years=1)) for t in final_df.index]

        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        
        final_df.to_csv(os.path.join(output_dir, "macro_indicators_raw.csv"))
        print(f"[SUCCESS] Data saved with Sector Signals.")
    except Exception as e:
        print(f"[ERROR] Sector download failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()