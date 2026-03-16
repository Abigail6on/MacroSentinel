import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import shap
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "rf_crash_predictor.pkl")

def export_shap_explanations(pipeline, X_latest_raw, feature_names, output_dir):
    """Extracts SHAP values to show the 'Why' behind the model's decision."""
    print("\n--- Generating SHAP Explainability Metrics ---")
    try:
        preprocessor = pipeline.named_steps['preprocessor']
        model = pipeline.named_steps['classifier']
        X_latest_processed = preprocessor.transform(X_latest_raw)
        
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_latest_processed)
        
        if isinstance(shap_values, list):
            shap_contribution = shap_values[1][0] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_contribution = shap_values[0]

        explanation = {name: round(float(val), 4) for name, val in zip(feature_names, shap_contribution)}
        
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "shap_explanation.json"), "w") as f:
            json.dump(explanation, f, indent=4)
        print(f"[SUCCESS] SHAP explanation saved.")
    except Exception as e:
        print(f"[WARNING] SHAP generation failed: {e}")

def train_predictor():
    print("--- Initializing Sentinel ML Training Engine ---")
    
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] No data found at {REGIME_DATA}")
        return

    # 1. Load Data
    df = pd.read_csv(REGIME_DATA, index_col="Timestamp", parse_dates=True)
    
    # --- 2. DYNAMIC COLUMN DETECTION ---
    potential_sent_cols = [c for c in df.columns if 'sentiment' in c.lower()]
    sent_col = potential_sent_cols[0] if potential_sent_cols else 'Inflation_Sentiment'

    # 3. FEATURE ENGINEERING 
    df['VIX_Momentum'] = df['VIX_Index'].pct_change(periods=3)
    df['Liquidity_Velocity'] = df['Real_Liquidity'].diff(periods=5) if 'Real_Liquidity' in df.columns else 0.0
    df['VIX_Rolling_Std'] = df['VIX_Index'].rolling(window=10).std()
    
    # Lags
    df['VIX_Lag1'] = df['VIX_Index'].shift(1)
    if sent_col in df.columns:
        df['Sentiment_Lag1'] = df[sent_col].shift(1)
    else:
        df['Sentiment_Lag1'] = 0.0
    
    # 4. Define Target (Crash = 15% VIX spike)
    forecast_horizon = 5
    df['Target_Crash'] = (df['VIX_Index'].shift(-forecast_horizon) > df['VIX_Index'] * 1.15).astype(int)
    
    df = df.dropna()

    # --- 5. ALIGNED FEATURE SET (The Big Fix) ---
    # We now explicitly include the rich data from your fixed CSV
    macro_features = [
        'VIX_Index', 'Real_Liquidity', 'Yield_Curve_10Y2Y', 'Fed_Funds_Rate', 
        'VIX_Momentum', 'Liquidity_Velocity', 'VIX_Rolling_Std', 'VIX_Lag1'
    ]
    nlp_features = [
        'Inflation_Sentiment', 'Labor_Market', 'Manufacturing', 'Monetary_Policy', 'Sentiment_Lag1'
    ]
    
    # Verify columns exist before training
    avail_features = [c for c in (macro_features + nlp_features) if c in df.columns]
    X = df[avail_features]
    y = df['Target_Crash']

    if len(X) < 20:
        print("[ERROR] Not enough data rows to train. Need at least 20 periods.")
        return

    # 6. Preprocessing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline([
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]), avail_features)
        ]
    )

    # 7. Model Competition
    rf_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', RandomForestClassifier(n_estimators=100, max_depth=7, random_state=42))])
    xgb_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', XGBClassifier(eval_metric='logloss', random_state=42))])

    # 8. Evaluation
    rf_pipeline.fit(X_train, y_train)
    xgb_pipeline.fit(X_train, y_train)
    
    rf_acc = accuracy_score(y_test, rf_pipeline.predict(X_test))
    xgb_acc = accuracy_score(y_test, xgb_pipeline.predict(X_test))

    print(f"Random Forest Accuracy: {rf_acc * 100:.2f}%")
    print(f"XGBoost Accuracy:       {xgb_acc * 100:.2f}%")

    # 9. Selection & Saving
    os.makedirs(MODEL_DIR, exist_ok=True)
    winner = xgb_pipeline if xgb_acc >= rf_acc else rf_pipeline
    winner_name = "XGBoost" if xgb_acc >= rf_acc else "Random Forest"
    
    joblib.dump(winner, MODEL_PATH)
    print(f"\n[SUCCESS] {winner_name} saved as production engine.")

    # 10. Explainability
    export_shap_explanations(winner, X.iloc[-1:], avail_features, os.path.join(BASE_DIR, "data", "processed"))

if __name__ == "__main__":
    train_predictor()