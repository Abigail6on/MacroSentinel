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

# CALIBRATION PARAMETERS
THRESHOLDS = {
    "Growth_Pulse": 0.15,
    "RSI_Overbought": 70,
    "RSI_Oversold": 30,
    "Inflation_Warning": 3.0
}

def calculate_rsi(series, period=14):
    """Calculates the 14-period RSI Speedometer"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print("[ERROR] Data files missing. Ensure collectors have run.")
        return

    # 1. Load and Sanitize
    macro_df = pd.read_csv(MACRO_RAW, index_col=0)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)
    
    # FORCED STANDARDIZATION: This fixes the Timeline Zero issue
    macro_df.index = pd.to_datetime(macro_df.index).tz_localize(None).astype('datetime64[ns]')
    news_df.index = pd.to_datetime(news_df.index).tz_localize(None).astype('datetime64[ns]')

    # 2. Precision Merge
    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # 3. THE INFLATION FIX: Calculate and Log
    if 'Inflation_CPI' in combined.columns and 'Inflation_CPI_LastYear' in combined.columns:
        combined['Inflation_YoY'] = ((combined['Inflation_CPI'] / combined['Inflation_CPI_LastYear']) - 1) * 100
        latest_inf = combined['Inflation_YoY'].iloc[-1]
        print(f"[INFO] Inflation Bridge active. Latest YoY: {latest_inf:.2f}%")
    else:
        print("[WARNING] Inflation Bridge column missing in CSV! Defaulting to 0.")
        combined['Inflation_YoY'] = 0

    # 4. TACTICAL RSI SPEEDOMETER
    if 'SPY' in combined.columns:
        combined['RSI'] = calculate_rsi(combined['SPY'])
    else:
        combined['RSI'] = 50

    regimes = []
    current_state = "Neutral / Transitioning"

    # 5. Decision Engine
    for i in range(len(combined)):
        row = combined.iloc[i]
        inf, rsi = row.get('Inflation_YoY', 0), row.get('RSI', 50)
        
        # Calculate Growth Pulse (Labor + Manufacturing weights)
        labor = row.get('Labor_Market', 0)
        mfg = row.get('Manufacturing', 0)
        growth_pulse = (labor * 0.6) + (mfg * 0.4)
        
        # --- LOGIC GATE ---
        if growth_pulse > THRESHOLDS["Growth_Pulse"]:
            # Check tactical RSI overlay
            if rsi > THRESHOLDS["RSI_Overbought"]:
                current_state = "Goldilocks (Overbought - Trim)"
            elif rsi < THRESHOLDS["RSI_Oversold"]:
                current_state = "Goldilocks (Oversold - Opportunity)"
            else:
                current_state = "Goldilocks (Growth)"
        else:
            current_state = "Neutral / Transitioning"
            
        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    
    # 6. Save with named index to prevent Performance Engine crashes
    combined.index.name = "Timestamp"
    combined.to_csv(OUTPUT_PATH)
    print(f"[SUCCESS] Final Regime State: {current_state} | RSI: {rsi:.1f}")

if __name__ == "__main__":
    determine_regime_v2()