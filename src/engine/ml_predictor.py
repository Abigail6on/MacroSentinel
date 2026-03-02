import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
MODEL_DIR = os.path.join(BASE_DIR, "data", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "rf_crash_predictor.pkl")

def train_predictor():
    print("--- Initializing Track 7: ML Predictive Alpha (Pipeline Architecture) ---")
    
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] Cannot find training data at {REGIME_DATA}")
        return
        
    df = pd.read_csv(REGIME_DATA)
    
    # 1. Feature Selection (Separating Macro vs NLP for the Pipeline)
    macro_features = ['VIX_Index', 'Yield_Curve_10Y2Y', 'Real_Liquidity']
    nlp_features = ['Inflation_Sentiment', 'Monetary_Policy', 'Labor_Market']
    
    avail_macro = [f for f in macro_features if f in df.columns]
    avail_nlp = [f for f in nlp_features if f in df.columns]
    available_features = avail_macro + avail_nlp
    
    # 2. Target Labeling (y)
    # We look 5 periods into the future
    forecast_horizon = 5
    df['Future_SPY'] = df['SPY'].shift(-forecast_horizon)
    df['Future_Return'] = (df['Future_SPY'] - df['SPY']) / df['SPY']
    df['Target_Crash'] = np.where(df['Future_Return'] < -0.01, 1, 0)
    
    # Drop rows where we don't have the Future Return yet
    ml_df = df.dropna(subset=available_features + ['Future_Return']).copy()
    
    if len(ml_df) < 50:
        print("[WARNING] Not enough historical data to train a robust ML model yet.")
        return

    X = ml_df[available_features]
    y = ml_df['Target_Crash']
    
    # 3. Time-Series Train/Test Split
    # shuffle=False prevents "look-ahead bias"
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    
    # 4. Build the Production Scikit-Learn Pipeline
    print(f"[INFO] Building ColumnTransformer & Training Pipeline on {len(X_train)} records...")
    
    # Step A: Macro data needs scaling because values range wildly (e.g., M2 Liquidity vs Yield Curve)
    macro_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # Step B: NLP data is already bounded (-1 to 1), so we just impute missing values
    nlp_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value=0.0))
    ])
    
    # Step C: Combine them into a ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('macro', macro_transformer, avail_macro),
            ('nlp', nlp_transformer, avail_nlp)
        ],
        remainder='drop'
    )
    
    # Step D: The Final Pipeline (Preprocessor -> ML Brain)
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, class_weight='balanced'))
    ])
    
    # 5. Train the Pipeline
    # The pipeline automatically scales the data using ONLY X_train, preventing data leakage
    model_pipeline.fit(X_train, y_train)
    
    # 6. Evaluate the Model
    # The pipeline automatically scales X_test using the parameters learned from X_train
    predictions = model_pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"\n[RESULTS] Pipeline Accuracy (Out-of-Sample): {accuracy * 100:.2f}%")
    
    # 7. Extract Feature Importances from the Pipeline
    print("\n[EXPLAINABLE AI] Feature Importances:")
    rf_model = model_pipeline.named_steps['classifier']
    ordered_features = avail_macro + avail_nlp
    for name, importance in zip(ordered_features, rf_model.feature_importances_):
        print(f" - {name}: {importance * 100:.2f}%")
    
    # 8. Save the Entire Pipeline
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model_pipeline, MODEL_PATH)
    print(f"\n[SUCCESS] Production ML Pipeline saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_predictor()