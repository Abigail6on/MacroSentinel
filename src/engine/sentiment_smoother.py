import pandas as pd
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

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
    df = pd.read_csv(INPUT_PATH, parse_dates=['Timestamp'])
    
    # 2. Advanced NLP Conviction Scoring
    if 'Headline' in df.columns:
        print("[INFO] VADER NLP Engine initialized. Calculating compound scores...")
        analyzer = SentimentIntensityAnalyzer()
        
        # Calculate raw compound score
        df['Vader_Compound'] = df['Headline'].apply(lambda x: analyzer.polarity_scores(str(x))['compound'])
        
        # Apply Intensity Multiplier for Market Conviction
        def apply_multiplier(score):
            if abs(score) >= 0.8:
                return score * 1.5  # High conviction / Extreme news
            elif abs(score) <= 0.2:
                return score * 0.5  # Low conviction / Noise reduction
            return score * 1.0      # Standard weighting
            
        df['Weighted_Sentiment'] = df['Vader_Compound'].apply(apply_multiplier)
        value_col = 'Weighted_Sentiment'
    else:
        print("[WARNING] 'Headline' column not found. Falling back to pre-calculated 'Sentiment'.")
        print("         -> Ensure news_collector.py saves the 'Headline' text in the future.")
        value_col = 'Sentiment'
    
    # 3. Pivot data to handle indicators as separate time-series
    pivot_df = df.pivot_table(
        index='Timestamp', 
        columns='Indicator', 
        values=value_col, 
        aggfunc='mean'
    ).sort_index()

    # 4. Apply a 6-period rolling mean to filter out high-frequency noise
    smoothed_df = pivot_df.rolling(window=6, min_periods=1).mean()
    smoothed_df = smoothed_df.ffill().dropna()

    # 5. Automated Directory Verification & Persistence
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    smoothed_df.to_csv(OUTPUT_PATH)
    
    print(f"[SUCCESS] Advanced NLP Smoothed signals saved to {OUTPUT_PATH}")
    print("\n--- LATEST SMOOTHED INDICATOR TRENDS ---")
    print(smoothed_df.tail(1).T)
    print("-----------------------------------------")

if __name__ == "__main__":
    smooth_signals()