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

THRESHOLDS = {
    "Goldilocks": {"Entry": 0.15, "Exit": 0.05},
    "Hawkish_Fed": {"Entry": -0.20, "Exit": -0.10},
    "Inflation_Risk": {"High": 3.5, "Target": 2.0},
    "Fear_Filter": 20.0,
    "Rotation_Sensitivity": 0.02,
    "RSI": {"Overbought": 70, "Oversold": 30}
}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        sys.exit(1)

    macro_df = pd.read_csv(MACRO_RAW, index_col=0)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)
    
    macro_df.index = pd.to_datetime(macro_df.index).tz_localize(None).astype('datetime64[ns]')
    news_df.index = pd.to_datetime(news_df.index).tz_localize(None).astype('datetime64[ns]')

    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # Defensive Calculations
    if 'Inflation_CPI_LastYear' in combined.columns:
        combined['Inflation_YoY'] = ((combined['Inflation_CPI'] / combined['Inflation_CPI_LastYear']) - 1) * 100
    else:
        combined['Inflation_YoY'] = 0

    if 'SPY' in combined.columns:
        combined['RSI'] = calculate_rsi(combined['SPY'])
    else:
        combined['RSI'] = 50

    regimes = []
    current_state = "Neutral / Transitioning"

    for i in range(len(combined)):
        row = combined.iloc[i]
        inf, rsi = row.get('Inflation_YoY', 0), row.get('RSI', 50)
        growth_pulse = (row.get('Labor_Market', 0) * 0.6) + (row.get('Manufacturing', 0) * 0.4)

        if inf > THRESHOLDS["Inflation_Risk"]["High"] and growth_pulse < 0:
            current_state = "Stagflation (High Risk)"
        elif growth_pulse > THRESHOLDS["Goldilocks"]["Entry"]:
            if rsi > THRESHOLDS["RSI"]["Overbought"]:
                current_state = "Goldilocks (Overbought - Trim)"
            elif rsi < THRESHOLDS["RSI"]["Oversold"]:
                current_state = "Goldilocks (Oversold - Opportunity)"
            else:
                current_state = "Goldilocks (Growth)"
        else:
            current_state = "Neutral / Transitioning"

        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    combined.to_csv(OUTPUT_PATH)
    print(f"[SUCCESS] Regime determined: {current_state}")

if __name__ == "__main__":
    determine_regime_v2()