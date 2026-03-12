import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("SUPABASE_URL")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

def push_latest_prediction_to_db():
    print("--- Initializing Sentinel Database Engine ---")
    
    if not DB_URL:
        print("[ERROR] SUPABASE_URL not found in .env file.")
        return

    # 1. Load the latest AI prediction from your CSV
    try:
        df = pd.read_csv(REGIME_PATH)
        latest_data = df.iloc[-1]
        
        # Extract the specific columns we want to save
        timestamp = latest_data["Timestamp"]
        regime = latest_data.get("Regime_V2", "Unknown")
        liquidity = float(latest_data.get("Real_Liquidity", 0.0))
        vix = float(latest_data.get("VIX_Index", 0.0))
        ml_veto = bool(latest_data.get("ML_Crash_Veto", False))
        strategy_val = float(latest_data.get("Strategy_Value", 100.0))
        
        print(f"[INFO] Preparing to push {timestamp} | Regime: {regime}")
        
    except Exception as e:
        print(f"[ERROR] Failed to load local data: {e}")
        return

    # 2. Connect to Cloud PostgreSQL and Execute SQL
    try:
        # Open the connection
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        # Write the raw SQL INSERT statement (Great for DA/PA interviews!)
        insert_query = """
            INSERT INTO historical_predictions 
            (timestamp, regime_v2, real_liquidity, vix_index, ml_crash_veto, strategy_value)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp) DO NOTHING;
        """
        
        # Execute the query with our data
        cursor.execute(insert_query, (timestamp, regime, liquidity, vix, ml_veto, strategy_val))
        
        # Commit the transaction and close the door
        conn.commit()
        cursor.close()
        conn.close()
        
        print("[SUCCESS] Data successfully committed to Supabase Cloud Database!")

    except Exception as e:
        print(f"[ERROR] Database connection or insertion failed: {e}")

if __name__ == "__main__":
    push_latest_prediction_to_db()