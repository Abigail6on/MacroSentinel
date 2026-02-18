import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
import ssl

# Fix for potential SSL certificate verification issues in restricted environments
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

# Mapping FRED codes to intuitive project indicator names
INDICATORS = {
    'CPIAUCSL': 'Inflation_CPI',
    'T10Y2Y': 'Yield_Curve_10Y2Y',
    'FEDFUNDS': 'Fed_Funds_Rate',
    'UNRATE': 'Unemployment_Rate',
    'VIXCLS': 'VIX_Index'
}

def fetch_macro_data():
    if not FRED_KEY:
        print("[ERROR] No FRED_API_KEY found. Ensure your .env file is configured.")
        return

    print("--- Phase C: Harvesting Macro, Sector, and Price Signals ---")
    fred = Fred(api_key=FRED_KEY)
    
    # 1. Fetch FULL FRED history
    # We retrieve the entire history to ensure the 'asof' logic can accurately
    # find anchor points for the Year-over-Year inflation calculation.
    macro_frames = []
    for code, name in INDICATORS.items():
        print(f"   [FETCHING FRED] {name}...")
        try:
            series = fred.get_series(code)
            macro_frames.append(pd.DataFrame({name: series}))
        except Exception as e:
            print(f"   [ERROR] Failed to fetch {code}: {e}")
    
    # Consolidate monthly macro indicators and forward-fill to normalize
    macro_df = pd.concat(macro_frames, axis=1, sort=False).ffill()

    # 2. Fetch Recent Market Data (Hourly)
    # Tickers include SPY for RSI tactical signals and XLF/XLU for sector health
    print("   [FETCHING MARKET] XLF, XLU, and SPY...")
    try:
        data = yf.download(["XLF", "XLU", "SPY"], period="1mo", interval="1h")
        
        # Extract 'Close' prices, handling potential MultiIndex from yfinance
        market_data = data['Close'] if isinstance(data.columns, pd.MultiIndex) else data
            
        # Standardize index to be timezone-naive for seamless merging
        market_data.index = market_data.index.tz_localize(None)
        
        # 3. DATA ALIGNMENT: Merge Monthly Macro onto Hourly Market Index
        # This reindexes the monthly macro facts to match the frequency of price data
        final_df = macro_df.reindex(market_data.index, method='ffill')
        
        # Integrate actual hourly prices into the master dataframe
        for ticker in ["XLF", "XLU", "SPY"]:
            if ticker in market_data.columns:
                final_df[ticker] = market_data[ticker]
        
        # 4. HISTORICAL INFLATION BRIDGE
        # This resolves the 0% inflation issue by locating the CPI value from exactly
        # 365 days prior for every single hourly timestamp in the current window.
        print("   [CALCULATING] Year-over-Year Inflation Anchor...")
        full_cpi_series = macro_df['Inflation_CPI']
        
        final_df['Inflation_CPI_LastYear'] = [
            full_cpi_series.asof(t - pd.DateOffset(years=1)) for t in final_df.index
        ]

        # 5. Output Management
        # Saves the file to the local data/raw directory relative to the project structure
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
        output_dir = os.path.join(BASE_DIR, "data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "macro_indicators_raw.csv")
        final_df.to_csv(output_path)
        print(f"[SUCCESS] Merged macro and market data saved to: {output_path}")

    except Exception as e:
        print(f"   [MARKET ERROR] Data processing failed: {e}")

if __name__ == "__main__":
    fetch_macro_data()