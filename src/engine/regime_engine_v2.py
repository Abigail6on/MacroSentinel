import pandas as pd
import os

# Environment-Agnostic Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
MACRO_RAW = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
SMOOTHED_NEWS = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print("[ERROR] Required data files missing. Ensure collectors and smoother have run.")
        return

    print("[INFO] Executing Regime Engine V2 (Multi-Factor Analysis)...")

    # 1. Load Hard Data (FRED)
    macro_df = pd.read_csv(MACRO_RAW, index_col=0, parse_dates=True)
    macro_df['Inflation_YoY'] = macro_df['Inflation_CPI'].pct_change(periods=12) * 100

    # 2. Load Soft Data (Smoothed News Trends)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0, parse_dates=True)

    # 3. Time-Series Alignment (Merge)
    combined = pd.merge_asof(
        news_df.sort_index(), 
        macro_df.sort_index(), 
        left_index=True, 
        right_index=True
    )

    # 4. Advanced Factor Logic
    def classify_v2(row):
        inf_yo_y = row.get('Inflation_YoY', 0)
        yield_spread = row.get('Yield_Curve_10Y2Y', 0)
        
        # Soft Metrics
        fed = row.get('Monetary_Policy', 0)
        labor = row.get('Labor_Market', 0)
        mfg = row.get('Manufacturing', 0)
        prices = row.get('Inflation_Sentiment', 0)

        # Composite Growth Pulse
        growth_pulse = (labor * 0.6) + (mfg * 0.4)
        
        # 1. RECESSION CHECK (Hard constraint)
        # If the yield curve is inverted AND growth news is negative
        if yield_spread < 0 and growth_pulse < 0:
            return "Deflationary Recession (Confirmed)"

        # 2. STAGFLATION CHECK
        if inf_yo_y > 3.5 and prices < -0.2 and growth_pulse < 0:
            return "Stagflation (High Risk)"

        # 3. GOLDILOCKS CHECK
        if 1.0 < inf_yo_y < 3.0 and growth_pulse > 0.1:
            if fed < -0.15: 
                return "Goldilocks -> Tightening (Warning)"
            return "Goldilocks (Growth)"

        return "Neutral / Transitioning"

    combined['Regime_V2'] = combined.apply(classify_v2, axis=1)

    # 5. Save and Export
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    combined.to_csv(OUTPUT_PATH)

    # Final Summary Report
    latest = combined.iloc[-1]
    print("\n--- MACRO SENTINEL V2.5 STATUS ---")
    print(f"Timestamp:       {combined.index[-1]}")
    print(f"Detected Regime:  {latest['Regime_V2']}")
    print(f"Growth Pulse:    {((labor * 0.6) + (mfg * 0.4)):.2f}")
    print(f"Inflation Press: {latest['Inflation_YoY'] + (abs(prices) if prices < 0 else 0):.2f}%")
    print(f"Fed Mood:        {latest.get('Monetary_Policy', 0):.2f}")
    print("----------------------------------")

if __name__ == "__main__":
    determine_regime_v2()