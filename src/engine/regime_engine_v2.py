import pandas as pd
import numpy as np
import os
import joblib
import warnings
from pandas.errors import PerformanceWarning

warnings.filterwarnings('ignore', category=PerformanceWarning)

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
    
    # Identify time column
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

    # Clean duplicates after floor rounding
    macro = macro[~macro.index.duplicated(keep='last')]
    
    # MERGE: We join on the macro index to ensure we don't lose rows
    if smoothed is not None:
        smoothed = smoothed[~smoothed.index.duplicated(keep='last')]
        combined = macro.join(smoothed, how='left')
    else:
        combined = macro

    # Remove ghost timestamp columns and handle gaps
    valid_cols = [c for c in combined.columns if not (('-' in str(c)) and (':' in str(c)))]
    combined = combined[valid_cols].ffill().fillna(0)

    # Base Feature Engineering
    combined['Real_Liquidity'] = combined['Liquidity_M2'].pct_change() - combined['Inflation_CPI'].pct_change()
    combined['Growth_Pulse'] = combined['SPY'].pct_change(periods=5)
    
    # ML Prediction Logic
    ml_veto_flags = [False] * len(combined)
    if os.path.exists(MODEL_PATH):
        try:
            model_pipeline = joblib.load(MODEL_PATH)
            
            # 1. Prepare Features
            features = combined.copy()
            features['VIX_Momentum'] = features['VIX_Index'].pct_change(periods=3)
            features['Liquidity_Velocity'] = features['Real_Liquidity'].diff(periods=5)
            features['VIX_Rolling_Std'] = features['VIX_Index'].rolling(window=10).std()
            features['VIX_Lag1'] = features['VIX_Index'].shift(1)
            
            if 'Inflation_Sentiment' in features.columns:
                features['Sentiment_Lag1'] = features['Inflation_Sentiment'].shift(1)

            # 2. DYNAMICALLY EXTRACT ALL REQUIRED FEATURES
            # Look through all steps in the ColumnTransformer to get every required column
            expected_features = []
            for name, transformer, cols in model_pipeline.named_steps['preprocessor'].transformers_:
                if name != 'remainder':
                    # Unpack if it's a list of lists
                    if len(cols) > 0 and isinstance(cols[0], list):
                        cols = [item for sublist in cols for item in sublist]
                    expected_features.extend(cols)
            
            # 3. Apply Feature Mocking for anything truly missing
            for feat in expected_features:
                if feat not in features.columns:
                    features[feat] = 0.0
            
            # Final data cleaning for the model
            X_input = features[expected_features].fillna(0)
            
            # 4. Generate Predictions
            ml_predictions = model_pipeline.predict(X_input)
            ml_veto_flags = [bool(p) for p in ml_predictions]
            
        except Exception as e:
            print(f"[WARNING] ML Prediction Engine skipped: {e}")

    # Final Regime Attribution
    regimes = []
    for i in range(len(combined)):
        if ml_veto_flags[i]:
            state = "Defensive (Contraction)"
        elif combined['Real_Liquidity'].iloc[i] < -1.0:
            state = "Stagflation"
        elif combined['Growth_Pulse'].iloc[i] > 0.15:
            state = "Goldilocks"
        else:
            state = "Neutral"
        regimes.append(state)

    # Persistence
    combined['Regime_V2'] = regimes
    combined['ML_Crash_Veto'] = ml_veto_flags
    combined.to_csv(OUTPUT_PATH, index=True, index_label="Timestamp")
    
    print(f"\n[SUCCESS] Engine Update Complete.")
    print(f" -> Current State: {regimes[-1]}")
    print(f" -> ML Veto Status: {'ACTIVE (Crash Detected)' if ml_veto_flags[-1] else 'Standby (Market Safe)'}")

if __name__ == "__main__":
    run_regime_engine()