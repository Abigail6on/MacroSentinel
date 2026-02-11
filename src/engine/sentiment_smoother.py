import pandas as pd
import os

# 1. Environment-Agnostic Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
INPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "news_stream_history.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")

def smooth_signals():
    if not os.path.exists(INPUT_PATH):
        print(f"[ERROR] No stream history found at {INPUT_PATH}. Run news_collector.py first.")
        return

    print("[INFO] Processing sentiment trends from stream history...")
    
    # 2. Load and pivot data to handle indicators as separate time-series
    df = pd.read_csv(INPUT_PATH, parse_dates=['Timestamp'])
    
    # Pivot ensures each indicator (e.g., Monetary_Policy) has its own column
    pivot_df = df.pivot_table(
        index='Timestamp', 
        columns='Indicator', 
        values='Sentiment', 
        aggfunc='mean'
    ).sort_index()

    # 3. Apply a 5-period rolling mean to filter out high-frequency noise
    # This transforms noisy daily/hourly headlines into a cleaner trend line
    smoothed_df = pivot_df.rolling(window=5, min_periods=1).mean()
    
    # Forward fill ensures continuity between collection cycles
    smoothed_df = smoothed_df.ffill().dropna()

    # 4. Automated Directory Verification
    # Ensures the data/processed directory exists before saving
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    smoothed_df.to_csv(OUTPUT_PATH)
    
    print(f"[SUCCESS] Smoothed signals saved to {OUTPUT_PATH}")
    print("\n--- LATEST SMOOTHED INDICATOR TRENDS ---")
    print(smoothed_df.tail(1).T)
    print("-----------------------------------------")

if __name__ == "__main__":
    smooth_signals()