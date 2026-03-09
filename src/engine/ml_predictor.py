import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
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
    """
    Extracts the model from a Scikit-Learn Pipeline and generates SHAP values.
    Dynamically handles 2D (XGBoost) and 3D (Random Forest) array structures.
    """
    print("\n--- Generating SHAP Explainability Metrics ---")
    
    preprocessor = pipeline.named_steps['preprocessor']
    model = pipeline.named_steps['classifier']
    
    X_latest_processed = preprocessor.transform(X_latest_raw)
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_latest_processed)
    
    if isinstance(shap_values, list):
        # Scikit-Learn RF (Older SHAP versions return a list per class)
        shap_values_target = np.array(shap_values[1]).flatten()
        base_value = explainer.expected_value[1]
    else:
        # XGBoost or newer SHAP versions return a Numpy Array
        shap_array = np.array(shap_values)
        
        if shap_array.ndim == 3:
            # Random Forest: Shape is (1_sample, N_features, 2_classes)
            # We want all features for Class 1 (Index 1)
            shap_values_target = shap_array[0, :, 1].flatten()
            base_value = explainer.expected_value[1]
        else:
            # XGBoost: Shape is (1_sample, N_features)
            shap_values_target = shap_array[0].flatten()
            base_value = explainer.expected_value

    # Ensure base_value is extracted cleanly as a single float
    if isinstance(base_value, (np.ndarray, list)):
        base_value = float(base_value[-1])
    else:
        base_value = float(base_value)
    
    # Map the SHAP values to feature names
    feature_contributions = {}
    for i, feature in enumerate(feature_names):
        feature_contributions[feature] = float(np.round(shap_values_target[i], 4))
        
    shap_payload = {
        "base_value": float(np.round(base_value, 4)),
        "contributions": feature_contributions
    }
    
    output_path = os.path.join(output_dir, "latest_shap.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(shap_payload, f, indent=4)
        
    print(f"[SUCCESS] SHAP explainability exported to {output_path}")

def train_predictor():
    print("--- Initializing Track 7: Champion vs Challenger ML Showdown ---")
    
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] Cannot find training data at {REGIME_DATA}")
        return
        
    df = pd.read_csv(REGIME_DATA)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values('Timestamp')
    
    # --- 1. MERGE NLP SENTIMENT ---
    SMOOTHED_PATH = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
    if os.path.exists(SMOOTHED_PATH):
        smooth_df = pd.read_csv(SMOOTHED_PATH)
        smooth_df['Timestamp'] = pd.to_datetime(smooth_df['Timestamp'])
        smooth_df = smooth_df.sort_values('Timestamp')
        df = pd.merge_asof(df, smooth_df, on='Timestamp', direction='backward')
        
    # --- 2. MERGE OPTIONS SENTIMENT (PUT/CALL RATIO) ---
    PCR_PATH = os.path.join(BASE_DIR, "data", "raw", "put_call_ratio.csv")
    if os.path.exists(PCR_PATH):
        pcr_df = pd.read_csv(PCR_PATH)
        pcr_df['Timestamp'] = pd.to_datetime(pcr_df['Timestamp'])
        pcr_df = pcr_df.sort_values('Timestamp')
        
        df = pd.merge_asof(df, pcr_df, on='Timestamp', direction='backward')
        
        # Fill missing historical options data with 1.0 (Neutral Market)
        if 'Put_Call_Ratio' in df.columns:
            df['Put_Call_Ratio'] = df['Put_Call_Ratio'].fillna(1.0)
            
    # Handle any remaining missing early data points
    df = df.ffill().bfill()
    
    # --- 3. FEATURE SELECTION ---
    macro_features = ['VIX_Index', 'Yield_Curve_10Y2Y', 'Real_Liquidity', 'Put_Call_Ratio']
    nlp_features = ['Inflation_Sentiment', 'Monetary_Policy', 'Labor_Market']
    
    avail_macro = [f for f in macro_features if f in df.columns]
    avail_nlp = [f for f in nlp_features if f in df.columns]
    available_features = avail_macro + avail_nlp
    
    # 4. Target Labeling (y)
    forecast_horizon = 5
    df['Future_SPY'] = df['SPY'].shift(-forecast_horizon)
    df['Future_Return'] = (df['Future_SPY'] - df['SPY']) / df['SPY']
    df['Target_Crash'] = np.where(df['Future_Return'] < -0.01, 1, 0)
    
    ml_df = df.dropna(subset=available_features + ['Future_Return']).copy()
    
    if len(ml_df) < 50:
        print("[WARNING] Not enough historical data to train robust ML models yet.")
        return

    X = ml_df[available_features]
    y = ml_df['Target_Crash']
    
    # 5. Time-Series Train/Test Split (No Look-Ahead Bias)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    # 6. Build the Preprocessor (Traffic Cop)
    macro_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    nlp_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=0.0))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('macro', macro_transformer, avail_macro),
            ('nlp', nlp_transformer, avail_nlp)
        ],
        remainder='drop'
    )
    
    # 7. Build the Competitors
    print(f"\n[INFO] Training models on {len(X_train)} records...")
    
    # Competitor 1: Random Forest (The Champion)
    rf_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight='balanced'))
    ])
    
    # Competitor 2: XGBoost (The Challenger)
    xgb_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', XGBClassifier(n_estimators=100, max_depth=5, random_state=42, eval_metric='logloss'))
    ])
    
    # 8. Train & Score Both Models
    rf_pipeline.fit(X_train, y_train)
    rf_preds = rf_pipeline.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)
    
    xgb_pipeline.fit(X_train, y_train)
    xgb_preds = xgb_pipeline.predict(X_test)
    xgb_acc = accuracy_score(y_test, xgb_preds)
    
    print("\n--- 🥊 SHOWDOWN RESULTS 🥊 ---")
    print(f"Random Forest Accuracy: {rf_acc * 100:.2f}%")
    print(f"XGBoost Accuracy:       {xgb_acc * 100:.2f}%")
    
    # 9. Crown the Winner and Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    if xgb_acc >= rf_acc:
        print("\n[WINNER] XGBoost is the new Champion! Upgrading predictive engine...")
        joblib.dump(xgb_pipeline, MODEL_PATH)
        winner_name = "XGBoost"
        model_to_inspect = xgb_pipeline.named_steps['classifier']
        winning_pipeline = xgb_pipeline
    else:
        print("\n[WINNER] Random Forest defended its title! Retaining current engine...")
        joblib.dump(rf_pipeline, MODEL_PATH)
        winner_name = "Random Forest"
        model_to_inspect = rf_pipeline.named_steps['classifier']
        winning_pipeline = rf_pipeline
        
    print(f"\n[EXPLAINABLE AI] What is driving {winner_name}'s decisions?")
    importances = model_to_inspect.feature_importances_
    ordered_features = avail_macro + avail_nlp
    
    for name, imp in zip(ordered_features, importances):
        print(f" -> {name.ljust(20)}: {imp * 100:>5.2f}%")
        
    print(f"\n[SUCCESS] {winner_name} Pipeline saved to {MODEL_PATH}")

    # --- TRIGGER SHAP ON THE WINNER ---
    X_latest_raw = X.iloc[-1:] # Grab the very last row of raw data
    
    export_shap_explanations(
        pipeline=winning_pipeline,
        X_latest_raw=X_latest_raw,
        feature_names=ordered_features,
        output_dir=os.path.join(BASE_DIR, "data", "processed")
    )

if __name__ == "__main__":
    train_predictor()