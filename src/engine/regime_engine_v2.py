import pandas as pd
import numpy as np
import os
import sys
import joblib
import warnings
from pandas.errors import PerformanceWarning

# Suppress harmless Pandas memory fragmentation warnings to keep production logs clean
warnings.filterwarnings('ignore', category=PerformanceWarning)

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
MACRO_RAW = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
SMOOTHED_NEWS = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

# TRACK 7: AI Model Path
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "rf_crash_predictor.pkl")

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
    macro_df = pd.read_csv(MACRO_RAW, index_col=0, parse_dates=True)
    news_df = pd.read_csv(SMOOTHED_NEWS, index_col=0)

    # Convert news to time-series dictionary (Index = Indicators, First Column = Scores)
    latest_news = news_df.iloc[:, 0].to_dict()

    # 2. Add News to Macro Grid
    # Using .assign() unpacks the dictionary and adds all columns simultaneously
    combined = macro_df.assign(**latest_news)

    # 3. RSI Calculation
    if 'QQQ' in combined.columns:
        combined['RSI'] = calculate_rsi(combined['QQQ'])
        
    # 4. Real Liquidity Math (YoY M2 Growth - YoY CPI Inflation)
    if 'Liquidity_M2' in combined.columns and 'Inflation_CPI' in combined.columns:
        # --- Memory Optimization: De-fragment before adding calculation columns ---
        combined = combined.copy()
        combined['M2_YoY'] = (combined['Liquidity_M2'] - combined['Liquidity_M2_LastYear']) / combined['Liquidity_M2_LastYear'] * 100
        combined['CPI_YoY'] = (combined['Inflation_CPI'] - combined['Inflation_CPI_LastYear']) / combined['Inflation_CPI_LastYear'] * 100
        combined['Real_Liquidity'] = combined['M2_YoY'] - combined['CPI_YoY']
    else:
        combined['Real_Liquidity'] = 0.0

    # ==========================================
    # TRACK 7: LOAD MACHINE LEARNING BRAIN
    # ==========================================
    ml_model = None
    if os.path.exists(MODEL_PATH):
        ml_model = joblib.load(MODEL_PATH)
        ml_features = ['VIX_Index', 'Yield_Curve_10Y2Y', 'Real_Liquidity', 
                       'Inflation_Sentiment', 'Monetary_Policy', 'Labor_Market']
    
    regimes = []
    ml_veto_flags = []
    
    # 5. DECISION TREE
    for i in range(len(combined)):
        row = combined.iloc[i]
        rsi = row.get('RSI', 50)
        real_liq = row.get('Real_Liquidity', 0)
        
        # Growth Pulse
        growth_pulse = (row.get('Labor_Market', 0) * 0.6) + (row.get('Manufacturing', 0) * 0.4)
        
        is_ml_veto = False
        
        # --- TRACK 7: ML PREDICTIVE VETO CHECK ---
        if ml_model is not None:
            try:
                # Extract the 6 exact features the AI was trained on
                X_current = pd.DataFrame([row[ml_features]]).fillna(0)
                # Ask the AI: 1 = Crash predicted, 0 = Safe
                crash_prediction = ml_model.predict(X_current)[0]
                
                if crash_prediction == 1:
                    is_ml_veto = True
            except KeyError:
                pass # If features are missing early in the historical data, skip ML
        
        ml_veto_flags.append(is_ml_veto)

        # --- HYBRID REGIME ASSIGNMENT ---
        if is_ml_veto:
            # The AI senses a massive crash imminent in the next 5 hours.
            current_state = "Defensive (Contraction)"
            
        elif real_liq < -1.0: 
            # Traditional Heuristic: Fed is draining money
            current_state = "Stagflation / Liquidity Trap"
        
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

    # --- Memory Optimization: De-fragment one last time before appending large lists ---
    combined = combined.copy()
    combined['Regime_V2'] = regimes
    combined['ML_Crash_Veto'] = ml_veto_flags
    combined.to_csv(OUTPUT_PATH, index=True, index_label="Timestamp")
    
    # Status Report
    liq_val = combined['Real_Liquidity'].iloc[-1]
    liq_status = "CRUNCH" if liq_val < -1.0 else "NORMAL"
    latest_regime = combined['Regime_V2'].iloc[-1]
    ml_status = "ACTIVE (CRASH IMMINENT)" if ml_veto_flags[-1] else "STANDBY (MARKET SAFE)"
    
    print(f"[SUCCESS] Regime Engine V2 Updated. Liquidity: {liq_val:.2f}% [{liq_status}]")
    if ml_model:
        print(f"[TRACK 7] ML Predictive Brain: {ml_status}")
    print(f"[LATEST REGIME] {latest_regime}")

if __name__ == "__main__":
    determine_regime_v2()