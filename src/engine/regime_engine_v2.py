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
    """Calculates the 14-period RSI Speedometer"""
    series = pd.to_numeric(series, errors='coerce')
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    loss = loss.replace(0, np.nan)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def determine_regime_v2():
    if not os.path.exists(MACRO_RAW) or not os.path.exists(SMOOTHED_NEWS):
        print("[ERROR] Missing input data. Run collectors first.")
        return

    # 1. Load Data
    macro_df = pd.read_csv(MACRO_RAW, index_col=0)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)
    
    macro_df.index = pd.to_datetime(macro_df.index).tz_localize(None).astype('datetime64[ns]')
    news_df.index = pd.to_datetime(news_df.index).tz_localize(None).astype('datetime64[ns]')

    # 2. PRE-CALCULATION
    if 'SPY' in macro_df.columns:
        macro_df['RSI'] = calculate_rsi(macro_df['SPY'])
    else:
        macro_df['RSI'] = 50

    # 3. Merge
    combined = pd.merge_asof(news_df.sort_index(), macro_df.sort_index(), 
                            left_index=True, right_index=True, direction='backward')

    # 4. MACRO CALCS (Inflation & Liquidity)
    # Inflation YoY
    if 'Inflation_CPI_LastYear' in combined.columns:
        combined['Inflation_YoY'] = ((combined['Inflation_CPI'] / combined['Inflation_CPI_LastYear']) - 1) * 100
    else:
        combined['Inflation_YoY'] = 0

    # --- PHASE D: LIQUIDITY ENGINE ---
    # Real Liquidity = M2 Growth - Inflation
    if 'Liquidity_M2' in combined.columns and 'Liquidity_M2_LastYear' in combined.columns:
        combined['M2_YoY'] = ((combined['Liquidity_M2'] / combined['Liquidity_M2_LastYear']) - 1) * 100
        combined['Real_Liquidity'] = combined['M2_YoY'] - combined['Inflation_YoY']
    else:
        # Fallback if M2 is missing (assume neutral)
        combined['Real_Liquidity'] = 0.0

    regimes = []
    
    # 5. DECISION TREE
    for i in range(len(combined)):
        row = combined.iloc[i]
        rsi = row.get('RSI', 50)
        real_liq = row.get('Real_Liquidity', 0)
        
        # Growth Pulse
        growth_pulse = (row.get('Labor_Market', 0) * 0.6) + (row.get('Manufacturing', 0) * 0.4)
        
        # --- THE UPGRADE: LIQUIDITY VETO ---
        # If Real Liquidity is negative, the Fed is draining money.
        # It doesn't matter if Growth is good. Without money, assets fall.
        if real_liq < -1.0: 
            current_state = "Liquidity Crunch (Defensive)"
        
        # Standard Logic
        elif growth_pulse > 0.15:
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
    combined.to_csv(OUTPUT_PATH, index=True, index_label="Timestamp")
    
    # Status Report
    liq_status = "CRUNCH" if combined['Real_Liquidity'].iloc[-1] < -1.0 else "NORMAL"
    print(f"[SUCCESS] Regime Engine V2 Updated. Liquidity: {combined['Real_Liquidity'].iloc[-1]:.2f}% [{liq_status}]")

if __name__ == "__main__":
    determine_regime_v2()