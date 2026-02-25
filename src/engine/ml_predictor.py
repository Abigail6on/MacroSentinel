import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "rf_crash_predictor.pkl")

def train_predictor():
    print("--- Initializing Track 7: ML Predictive Alpha ---")
    
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] Cannot find training data at {REGIME_DATA}")
        return
        
    df = pd.read_csv(REGIME_DATA)
    
    # 1. Feature Selection (X) 
    features = ['VIX_Index', 'Yield_Curve_10Y2Y', 'Real_Liquidity', 
                'Inflation_Sentiment', 'Monetary_Policy', 'Labor_Market']
    available_features = [f for f in features if f in df.columns]
    
    # 2. Target Labeling (y)
    # We look 5 periods (hours) into the future
    forecast_horizon = 5
    df['Future_SPY'] = df['SPY'].shift(-forecast_horizon)
    df['Future_Return'] = (df['Future_SPY'] - df['SPY']) / df['SPY']
    
    # Label = 1 (CRASH RISK) if the market drops, 0 (SAFE) if it goes up
    df['Target_Crash'] = np.where(df['Future_Return'] < 0, 1, 0)
    
    # Drop rows at the end that don't have future data yet
    ml_df = df.dropna(subset=available_features + ['Future_Return']).copy()
    
    if len(ml_df) < 50:
        print("[WARNING] Not enough historical data to train a robust ML model yet.")
        return

    X = ml_df[available_features]
    y = ml_df['Target_Crash']
    
    # 3. Time-Series Train/Test Split
    # We use shuffle=False to prevent "look-ahead bias" (training on the future to predict the past)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    # 4. Train the Random Forest
    print(f"[INFO] Training Random Forest on {len(X_train)} historical records...")
    # class_weight='balanced' helps the AI care equally about crashes and rallies
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    
    # 5. Evaluate the Model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"\n[RESULTS] Model Accuracy (Out-of-Sample): {accuracy * 100:.2f}%")
    
    print("\n[EXPLAINABLE AI] Feature Importances:")
    for name, importance in zip(available_features, model.feature_importances_):
        print(f"  -> {name.ljust(20)}: {importance * 100:>5.2f}%")
        
    # 6. Save (Pickle) the Model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n[SUCCESS] AI Brain saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_predictor()