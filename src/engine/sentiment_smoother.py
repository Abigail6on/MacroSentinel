import pandas as pd
import os

# Configuration
INPUT_PATH = "../../data/raw/news_stream_history.csv"
OUTPUT_PATH = "../../data/processed/smoothed_indicators.csv"

def smooth_signals():
    if not os.path.exists(INPUT_PATH):
        print("[ERROR] No stream history found. Run news_collector.py first.")
        return

    print("[INFO] Processing sentiment trends...")
    
    # Load and pivot data to handle indicators as separate time-series
    df = pd.read_csv(INPUT_PATH, parse_dates=['Timestamp'])
    pivot_df = df.pivot_table(
        index='Timestamp', 
        columns='Indicator', 
        values='Sentiment', 
        aggfunc='mean'
    ).sort_index()

    # Apply 5-period rolling mean to filter out high-frequency noise
    smoothed_df = pivot_df.rolling(window=5, min_periods=1).mean()
    
    # Forward fill to ensure continuity between collection cycles
    smoothed_df = smoothed_df.ffill().dropna()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    smoothed_df.to_csv(OUTPUT_PATH)
    
    print(f"[SUCCESS] Smoothed signals saved to {OUTPUT_PATH}")
    print("\n--- LATEST SMOOTHED INDICATORS ---")
    print(smoothed_df.tail(1).T)

if __name__ == "__main__":
    smooth_signals()