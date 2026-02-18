import pandas as pd
import numpy as np
import os
import sys

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
MACRO_RAW = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
SMOOTHED_NEWS = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

def calculate_rsi(series, period=14):
    """Calculates the 14-period RSI Speedometer for Tactical RSI logic"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print("[ERROR] Missing input data. Run collectors first.")
        return

    # 1. Load Data
    macro_df = pd.read_csv(MACRO_RAW, index_col=0)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)
    
    # PRECISION FIX: Standardize to Nanoseconds to resolve 'Timeline Zero' errors
    macro_df.index = pd.to_datetime(macro_df.index).tz_localize(None).astype('datetime64[ns]')
    news_df.index = pd.to_datetime(news_df.index).tz_localize(None).astype('datetime64[ns]')

    # 2. Merge - Aligning Monthly Macro data onto the Hourly Sentiment grid
    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # 3. THE INFLATION BRIDGE FIX
    # 
    if 'Inflation_CPI_LastYear' in combined.columns:
        combined['Inflation_YoY'] = ((combined['Inflation_CPI'] / combined['Inflation_CPI_LastYear']) - 1) * 100
    else:
        combined['Inflation_YoY'] = 0

    # 4. TACTICAL RSI CALCULATION (Phase C)
    # 
    combined['RSI'] = calculate_rsi(combined['SPY']) if 'SPY' in combined.columns else 50

    regimes = []
    current_state = "Neutral / Transitioning"

    # 5. Regime Logic Loop
    for i in range(len(combined)):
        row = combined.iloc[i]
        inf, rsi = row.get('Inflation_YoY', 0), row.get('RSI', 50)
        
        # Calculate the Growth Pulse (Weighted Labor and Manufacturing)
        growth_pulse = (row.get('Labor_Market', 0) * 0.6) + (row.get('Manufacturing', 0) * 0.4)
        
        # Phase C: State Logic with Tactical RSI Overlays
        if growth_pulse > 0.15:
            if rsi > 70: 
                current_state = "Goldilocks (Overbought - Trim)"
            elif rsi < 30: 
                current_state = "Goldilocks (Oversold - Opportunity)"
            else: 
                current_state = "Goldilocks (Growth)"
        else:
            current_state = "Neutral / Transitioning"
            
        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    
    # Save the output with the Timestamp preserved as a column
    combined.to_csv(OUTPUT_PATH, index=True, index_label="Timestamp")
    print(f"[SUCCESS] Engine complete. Latest Inflation: {inf:.2f}% | State: {current_state}")

if __name__ == "__main__":
    determine_regime_v2()