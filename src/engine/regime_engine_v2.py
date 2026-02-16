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
    "Rotation_Sensitivity": 0.02 
}

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print(f"[ERROR] Missing data files.")
        sys.exit(1)

    print("[INFO] Phase B: Calculating Inflation YoY and Applying Sector Filter...")

    # 1. Load Data
    macro_df = pd.read_csv(MACRO_RAW, index_col=0)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)

    # Since FRED data is monthly, a 12-month change gives us the YoY %
    # Use the pre-fetched historical CPI to calculate YoY even with limited rows
    if 'Inflation_CPI' in macro_df.columns and 'Inflation_CPI_LastYear' in macro_df.columns:
        macro_df['Inflation_YoY'] = ((macro_df['Inflation_CPI'] / macro_df['Inflation_CPI_LastYear']) - 1) * 100
    else:
        macro_df['Inflation_YoY'] = 0 # Fallback
    
    # Standardize precision to [ns] to fix the previous MergeError
    macro_df.index = pd.to_datetime(macro_df.index).tz_localize(None).astype('datetime64[ns]')
    news_df.index = pd.to_datetime(news_df.index).tz_localize(None).astype('datetime64[ns]')

    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # 2. Sector Ratio Logic (XLF / XLU)
    combined['Sector_Ratio'] = combined['XLF'] / combined['XLU']
    combined['Ratio_Trend'] = combined['Sector_Ratio'].pct_change(6) 

    regimes = []
    current_state = "Neutral / Transitioning"

    for i in range(len(combined)):
        row = combined.iloc[i]
        
        # Signals (Now with the calculated Inflation_YoY)
        inf = row.get('Inflation_YoY', 0)
        fed = row.get('Monetary_Policy', 0)
        vix = row.get('VIX_Index', 0)
        ratio_trend = row.get('Ratio_Trend', 0)
        growth_pulse = (row.get('Labor_Market', 0) * 0.6) + (row.get('Manufacturing', 0) * 0.4)

        # A. DEFENSIVE REGIMES
        if inf < THRESHOLDS["Inflation_Risk"]["Target"] and growth_pulse < -0.1:
            current_state = "Deflationary Recession"
        elif inf > THRESHOLDS["Inflation_Risk"]["High"] and growth_pulse < 0:
            current_state = "Stagflation (High Risk)"

        # B. GROWTH REGIMES
        else:
            if growth_pulse > THRESHOLDS["Goldilocks"]["Entry"]:
                # Phase B Truth Filter: Check if sectors agree with news
                if ratio_trend < -THRESHOLDS["Rotation_Sensitivity"]:
                    current_state = "Neutral / Transitioning"
                else:
                    current_state = "Goldilocks (Growth)"
            
            elif growth_pulse < THRESHOLDS["Goldilocks"]["Exit"]:
                current_state = "Neutral / Transitioning"

            if current_state == "Goldilocks (Growth)":
                if fed < THRESHOLDS["Hawkish_Fed"]["Entry"] and vix > THRESHOLDS["Fear_Filter"]:
                     current_state = "Goldilocks -> Tightening (Warning)"

        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    
    # Save processed data (Dashboard will now find 'Inflation_YoY' here)
    combined.to_csv(OUTPUT_PATH)
    print(f"[SUCCESS] Regime History updated. Final State: {current_state}")

if __name__ == "__main__":
    determine_regime_v2()