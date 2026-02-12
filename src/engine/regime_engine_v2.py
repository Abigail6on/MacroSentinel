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
    "Inflation_Risk": {"High": 3.5, "Target": 2.0}
}

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print(f"[ERROR] Missing data files. Ensure collectors have run.")
        sys.exit(1)

    print("[INFO] Calibrating Signals & Determining Regime...")

    # Load and Merge
    macro_df = pd.read_csv(MACRO_RAW, index_col=0, parse_dates=True)
    macro_df['Inflation_YoY'] = macro_df['Inflation_CPI'].pct_change(periods=12) * 100
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0, parse_dates=True)
    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), left_index=True, right_index=True)

    regimes = []
    current_state = "Neutral / Transitioning"

    for _, row in combined.iterrows():
        inf = row.get('Inflation_YoY', 0)
        yield_spread = row.get('Yield_Curve_10Y2Y', 0)
        fed = row.get('Monetary_Policy', 0)
        labor = row.get('Labor_Market', 0)
        mfg = row.get('Manufacturing', 0)
        growth_pulse = (labor * 0.6) + (mfg * 0.4)

        # 1. RECESSION LOGIC
        if yield_spread < 0 and growth_pulse < -0.1:
            current_state = "Deflationary Recession"
        
        # 2. STAGFLATION LOGIC
        elif inf > THRESHOLDS["Inflation_Risk"]["High"] and growth_pulse < 0:
            current_state = "Stagflation (High Risk)"

        # 3. GROWTH REGIMES WITH HYSTERESIS
        else:
            if current_state == "Goldilocks (Growth)":
                if growth_pulse < THRESHOLDS["Goldilocks"]["Exit"] or fed < THRESHOLDS["Hawkish_Fed"]["Entry"]:
                    current_state = "Neutral / Transitioning"
            
            elif current_state == "Neutral / Transitioning":
                if growth_pulse > THRESHOLDS["Goldilocks"]["Entry"] and fed > THRESHOLDS["Hawkish_Fed"]["Exit"]:
                    current_state = "Goldilocks (Growth)"
            
            # Sub-state warning logic
            if current_state == "Goldilocks (Growth)" and fed < THRESHOLDS["Hawkish_Fed"]["Exit"]:
                 current_state = "Goldilocks -> Tightening (Warning)"

        regimes.append(current_state)

    combined['Regime_V2'] = regimes
    combined.to_csv(OUTPUT_PATH)
    
    print(f"--- CALIBRATION COMPLETE ---")
    print(f"Final Regime: {current_state}")
    print(f"Growth Pulse: {growth_pulse:.2f} | Fed Sentiment: {fed:.2f}")

if __name__ == "__main__":
    determine_regime_v2()