import pandas as pd
import numpy as np
import os

# Configuration
MACRO_DATA = "../../data/raw/macro_indicators_raw.csv"
NEWS_DATA = "../../data/raw/news_sentiment_raw.csv"
OUTPUT_PATH = "../../data/processed/macro_regime_status.csv"

def classify_regime(row):
    """
    Logic for 4 Macro Regimes:
    1. Goldilocks: High Growth/Low Inflation
    2. Overheat: High Growth/High Inflation 
    3. Stagflation: Low Growth/High Inflation
    4. Recession: Low Growth/Low Inflation
    """
    # Thresholds for initial classification
    inflation_high = row['Inflation_CPI_YoY'] > 3.0
    yield_curve_inverted = row['Yield_Curve_10Y2Y'] < 0
    
    if not inflation_high and not yield_curve_inverted:
        return "Goldilocks (Growth)"
    elif inflation_high and not yield_curve_inverted:
        return "Overheat (Inflationary)"
    elif inflation_high and yield_curve_inverted:
        return "Stagflation (Crisis)"
    else:
        return "Recession/Deflation (Safe Haven)"

def process_regime_engine():
    if not os.path.exists(MACRO_DATA) or not os.path.exists(NEWS_DATA):
        print("[ERROR] Missing input files. Ensure collectors have been executed.")
        return

    print("[INFO] Merging Macro and Sentiment datasets...")
    
    # 1. Load Data - Fixed index_col parameter
    macro_df = pd.read_csv(MACRO_DATA, index_col=0, parse_dates=True)
    news_df = pd.read_csv(NEWS_DATA, parse_dates=['Date'])
    
    # 2. Process Macro Data
    # Calculate Year-over-Year Inflation percentage change
    macro_df['Inflation_CPI_YoY'] = macro_df['Inflation_CPI'].pct_change(periods=12) * 100
    
    # 3. Process News Data
    # Aggregate sentiment by day
    daily_sentiment = news_df.groupby(news_df['Date'].dt.date)['Sentiment'].mean().to_frame('Avg_Sentiment')
    daily_sentiment.index = pd.to_datetime(daily_sentiment.index)

    # 4. Merge Logic
    # Use merge_asof to align monthly economic data with daily sentiment timestamps
    combined = pd.merge_asof(daily_sentiment.sort_index(), 
                            macro_df.sort_index(), 
                            left_index=True, 
                            right_index=True)
    
    # 5. Apply Regime Classification
    combined['Regime'] = combined.apply(classify_regime, axis=1)
    
    # 6. Save Processed Results
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    combined.to_csv(OUTPUT_PATH)
    
    # Summary of current conditions
    current_regime = combined['Regime'].iloc[-1]
    last_sentiment = combined['Avg_Sentiment'].iloc[-1]
    last_yield = combined['Yield_Curve_10Y2Y'].iloc[-1]
    
    print("\n--- CURRENT MACRO ENVIRONMENT ---")
    print(f"Status: {current_regime}")
    print(f"Average Sentiment: {last_sentiment:.2f}")
    print(f"Yield Curve Spread: {last_yield:.2f}")
    print("---------------------------------")
    print(f"[SUCCESS] Regime data saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    process_regime_engine()