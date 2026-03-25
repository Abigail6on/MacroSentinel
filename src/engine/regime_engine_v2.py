import pandas as pd
import numpy as np
import os
import joblib
import warnings
from pandas.errors import PerformanceWarning

warnings.filterwarnings('ignore', category=PerformanceWarning)
warnings.filterwarnings('ignore', category=UserWarning, module='xgboost')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
MACRO_RAW = os.path.join(BASE_DIR, "data", "raw", "macro_indicators_raw.csv")
SMOOTHED_NEWS = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "rf_crash_predictor.pkl")

def load_safely(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    
    time_options = ['Datetime', 'Timestamp', 'timestamp', 'Date']
    found_col = next((c for c in time_options if c in df.columns), None)
    
    if found_col:
        df = df.set_index(found_col)
    else:
        df = df.set_index(df.columns[0])
    
    df.index = pd.to_datetime(df.index)
    df.index = df.index.floor('h')
    return df

def run_regime_engine():
    print("--- Initializing Sentinel Regime Engine V2 ---")
    
    macro = load_safely(MACRO_RAW)
    smoothed = load_safely(SMOOTHED_NEWS)

    if macro is None:
        print("[ERROR] Macro data (macro_indicators_raw.csv) not found.")
        return

    macro = macro[~macro.index.duplicated(keep='last')]
    
    if smoothed is not None:
        smoothed = smoothed[~smoothed.index.duplicated(keep='last')]
        combined = macro.join(smoothed, how='left')
    else:
        combined = macro

    valid_cols = [c for c in combined.columns if not (('-' in str(c)) and (':' in str(c)))]
    combined = combined[valid_cols].ffill().fillna(0)

    # VULNERABILITY FIX: Safe base feature calculations to prevent KeyError if APIs fail
    if 'Liquidity_M2' in combined.columns and 'Inflation_CPI' in combined.columns:
        combined['Real_Liquidity'] = combined['Liquidity_M2'].pct_change() - combined['Inflation_CPI'].pct_change()
    else:
        print("[WARNING] Missing FRED data. Defaulting Real_Liquidity to NaN.")
        combined['Real_Liquidity'] = np.nan

    if 'SPY' in combined.columns:
        combined['Growth_Pulse'] = combined['SPY'].pct_change(periods=5)
    else:
        print("[WARNING] Missing Yahoo data. Defaulting Growth_Pulse to NaN.")
        combined['Growth_Pulse'] = np.nan
    
    ml_veto_flags = [False] * len(combined)
    if os.path.exists(MODEL_PATH):
        try:
            model_pipeline = joblib.load(MODEL_PATH)
            
            features = combined.copy()
            
            if 'VIX_Index' in features.columns:
                features['VIX_Momentum'] = features['VIX_Index'].pct_change(periods=3)
                features['VIX_Rolling_Std'] = features['VIX_Index'].rolling(window=10).std()
                features['VIX_Lag1'] = features['VIX_Index'].shift(1)
            else:
                features['VIX_Momentum'] = np.nan
                features['VIX_Rolling_Std'] = np.nan
                features['VIX_Lag1'] = np.nan
                
            features['Liquidity_Velocity'] = features['Real_Liquidity'].diff(periods=5)
            
            if 'Inflation_Sentiment' in features.columns:
                features['Sentiment_Lag1'] = features['Inflation_Sentiment'].shift(1)

            expected_features = []
            for name, transformer, cols in model_pipeline.named_steps['preprocessor'].transformers_:
                if name != 'remainder':
                    if len(cols) > 0 and isinstance(cols[0], list):
                        cols = [item for sublist in cols for item in sublist]
                    expected_features.extend(cols)
            
            for feat in expected_features:
                if feat not in features.columns:
                    features[feat] = np.nan
            
            X_input = features[expected_features]
            
            ml_predictions = model_pipeline.predict(X_input)
            ml_veto_flags = [bool(p) for p in ml_predictions]
            
        except Exception as e:
            print(f"[WARNING] ML Prediction Engine skipped: {e}")

    if combined.empty or len(combined) == 0:
        print("[WARNING] No valid data available to calculate regimes. Preserving previous state.")
        return 

    regimes = []
    for i in range(len(combined)):
        if ml_veto_flags[i]:
            state = "Defensive (Contraction)"
        elif pd.notna(combined['Real_Liquidity'].iloc[i]) and combined['Real_Liquidity'].iloc[i] < -1.0:
            state = "Stagflation"
        elif pd.notna(combined['Growth_Pulse'].iloc[i]) and combined['Growth_Pulse'].iloc[i] > 0.15:
            state = "Goldilocks"
        else:
            state = "Neutral"
        regimes.append(state)

    combined['Regime_V2'] = regimes
    combined['ML_Crash_Veto'] = ml_veto_flags
    
    MAX_ROWS = 1000
    if len(combined) > MAX_ROWS:
        combined = combined.tail(MAX_ROWS)

    combined.to_csv(OUTPUT_PATH, index=True, index_label="Timestamp")
    
    print(f"\n[SUCCESS] Engine Update Complete.")
    print(f" -> Current State: {regimes[-1]}")
    print(f" -> ML Veto Status: {'ACTIVE (Crash Detected)' if ml_veto_flags[-1] else 'Standby (Market Safe)'}")

if __name__ == "__main__":
    run_regime_engine()