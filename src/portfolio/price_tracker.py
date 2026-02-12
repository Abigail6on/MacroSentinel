import pandas as pd
import yfinance as yf
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PRICE_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "live_prices.csv")

def track_prices():
    # The core assets we mapped in our Allocator
    tickers = ["QQQ", "SPY", "XLE", "GLD", "TLT", "DBC", "XLU", "SHY"]
    
    print(f"[INFO] Fetching live market prices for {len(tickers)} assets...")
    
    try:
        # Fetch last 5 days of data to ensure we get the latest close
        data = yf.download(tickers, period="5d", interval="1d")['Close']
        
        # Get the most recent non-null price for each
        latest_prices = data.iloc[-1].to_frame(name="Price")
        
        # Calculate 24h Change %
        prev_prices = data.iloc[-2]
        latest_prices['Change_Pct'] = ((latest_prices['Price'] - prev_prices) / prev_prices) * 100
        
        os.makedirs(os.path.dirname(PRICE_DATA_PATH), exist_ok=True)
        latest_prices.to_csv(PRICE_DATA_PATH)
        print(f"[SUCCESS] Live prices saved to {PRICE_DATA_PATH}")
        
    except Exception as e:
        print(f"[ERROR] Price fetch failed: {e}")

if __name__ == "__main__":
    track_prices()