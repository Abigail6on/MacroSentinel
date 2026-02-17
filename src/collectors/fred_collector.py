import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

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
    print("--- Phase C: Harvesting Macro & Market Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL Macro History (Monthly)
    macro_frames = []
    for code, name in INDICATORS.items():
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"   [FRED ERROR] {name}: {e}")
    
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    # 2. Fetch Recent Market Data (Hourly)
    print("   [FETCHING] XLF, XLU, and SPY...")
    try:
        data = yf.download(["XLF", "XLU", "SPY"], period="1mo", interval="1h")
        
        # Extract 'Close' prices
        if isinstance(data.columns, pd.MultiIndex):
            market_data = data['Close']
        else:
            market_data = data
            
        market_data.index = market_data.index.tz_localize(None)
        
        # 3. THE BRIDGE: Align Monthly Macro to Hourly Market
        final_df = macro_df.reindex(market_data.index, method='ffill')
        
        # Add the actual hourly prices
        for ticker in ["XLF", "XLU", "SPY"]:
            if ticker in market_data.columns:
                final_df[ticker] = market_data[ticker]
        
        # 4. INFLATION BRIDGE: Look back exactly 1 year for every hour
        full_cpi_series = macro_df['Inflation_CPI']
        final_df['Inflation_CPI_LastYear'] = [
            full_cpi_series.asof(t - pd.DateOffset(years=1)) for t in final_df.index
        ]

        # 5. Save to Project Root
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(ROOT_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        
        final_df.to_csv(os.path.join(output_dir, "macro_indicators_raw.csv"))
        print(f"[SUCCESS] Saved hourly merged data to macro_indicators_raw.csv")

    except Exception as e:
        print(f"   [MARKET ERROR] {e}")

if __name__ == "__main__":
    fetch_macro_data()