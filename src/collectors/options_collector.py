import yfinance as yf
import pandas as pd
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "put_call_ratio.csv")

def fetch_options_sentiment():
    print("--- Fetching Options Market Sentiment (Put/Call Ratio) ---")
    
    spy = yf.Ticker("SPY")
    
    try:
        expirations = spy.options
    except Exception as e:
        print(f"[ERROR] Could not fetch options data from Yahoo Finance: {e}")
        return
        
    if not expirations:
        print("[WARNING] No options expirations found. Market data may be delayed.")
        return

    total_put_oi = 0
    total_call_oi = 0
    
    # We aggregate the 3 nearest expiration dates to capture immediate market panic
    for date in expirations[:3]:
        chain = spy.option_chain(date)
        
        # .sum() safely handles any NaN values in the openInterest column
        total_put_oi += chain.puts['openInterest'].sum()
        total_call_oi += chain.calls['openInterest'].sum()

    if total_call_oi == 0:
        pcr = 1.0  # Fallback to a neutral 1.0 ratio if data is missing
    else:
        pcr = total_put_oi / total_call_oi

    print(f"Total Put Open Interest:  {total_put_oi:,.0f}")
    print(f"Total Call Open Interest: {total_call_oi:,.0f}")
    print(f"SPY Put/Call Ratio:       {pcr:.4f}")

    # Save to the raw data directory
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    new_data = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Put_Call_Ratio": round(pcr, 4)
    }])
    
    # Append to existing history if the file exists, otherwise create it
    if os.path.exists(OUTPUT_PATH):
        existing_df = pd.read_csv(OUTPUT_PATH)
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        updated_df.to_csv(OUTPUT_PATH, index=False)
    else:
        new_data.to_csv(OUTPUT_PATH, index=False)
        
    print(f"[SUCCESS] Put/Call Ratio saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_options_sentiment()