import pandas as pd
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
    "Goldilocks": {"Entry": 0.15, "Exit": 0.05},
    "Hawkish_Fed": {"Entry": -0.20, "Exit": -0.10},
    "Inflation_Risk": {"High": 3.5, "Target": 2.0},
    "Fear_Filter": 20.0,
    "Rotation_Sensitivity": 0.02 # 2% change in XLF/XLU ratio is significant
}

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print(f"[ERROR] Missing data files.")
        sys.exit(1)

    print("[INFO] Phase B: Applying Sector Rotation Truth Filter...")

    # 1. Load Data
    macro_df = pd.read_csv(MACRO_RAW, index_col=0, parse_dates=True)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0, parse_dates=True)
    
    # Ensure all timestamps are standardized to avoid merge issues
    macro_df.index = macro_df.index.tz_localize(None)
    news_df.index = news_df.index.tz_localize(None)

    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # 2. Sector Ratio Logic (XLF / XLU)
    # XLF/XLU Ratio Rising = Market expects high rates (Growth/Inflation)
    # XLF/XLU Ratio Falling = Market expects rate cuts (Slowdown/Recession)
    combined['Sector_Ratio'] = combined['XLF'] / combined['XLU']
    combined['Ratio_Trend'] = combined['Sector_Ratio'].pct_change(6) # 6-hour trend

    regimes = []
    current_state = "Neutral / Transitioning"

    for i in range(len(combined)):
        row = combined.iloc[i]
        
        # Signals
        inf = row['Inflation_YoY']
        fed = row['Monetary_Policy']
        vix = row['VIX_Index']
        ratio_trend = row['Ratio_Trend']
        growth_pulse = (row['Labor_Market'] * 0.6) + (row['Manufacturing'] * 0.4)

        # A. DEFENSIVE REGIMES (Recession & Stagflation)
        if inf < THRESHOLDS["Inflation_Risk"]["Target"] and growth_pulse < -0.1:
            current_state = "Deflationary Recession"
        elif inf > THRESHOLDS["Inflation_Risk"]["High"] and growth_pulse < 0:
            current_state = "Stagflation (High Risk)"

        # B. GROWTH REGIMES
        else:
            # Entry into Goldilocks
            if growth_pulse > THRESHOLDS["Goldilocks"]["Entry"]:
                # --- PHASE B TRUTH FILTER ---
                # Even if news is good, if XLF/XLU ratio is crashing, it's a "Fake Out"
                if ratio_trend < -THRESHOLDS["Rotation_Sensitivity"]:
                    current_state = "Neutral / Transitioning"
                else:
                    current_state = "Goldilocks (Growth)"
            
            # Exit Logic
            elif growth_pulse < THRESHOLDS["Goldilocks"]["Exit"]:
                current_state = "Neutral / Transitioning"

            # Fear Filter
            if current_state == "Goldilocks (Growth)":
                if fed < THRESHOLDS["Hawkish_Fed"]["Entry"] and vix > THRESHOLDS["Fear_Filter"]:
                     current_state = "Goldilocks -> Tightening (Warning)"

        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    combined.to_csv(OUTPUT_PATH)
    print(f"[SUCCESS] Regime History updated with Sector Filter. Final State: {current_state}")

if __name__ == "__main__":
    determine_regime_v2()