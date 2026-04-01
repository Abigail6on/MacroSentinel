import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Prefer a clearly named database connection variable.
DB_URL = os.getenv("SUPABASE_DB_URL")

# Resolve project paths safely
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent.parent
REGIME_PATH = BASE_DIR / "data" / "processed" / "regime_v2_status.csv"

# Safer: keep server-only tables outside the public schema
TARGET_TABLE = "private.historical_predictions"


def _to_bool(value: Any) -> bool:
    """
    Convert common CSV/string/numeric values into a Python boolean.
    """
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    value_str = str(value).strip().lower()
    return value_str in {"true", "1", "yes", "y", "t"}


def _load_latest_prediction() -> tuple:
    """
    Load the latest row from the processed CSV and map it to the DB fields.
    Returns:
        (timestamp, regime, liquidity, vix, ml_veto, strategy_val)
    """
    if not REGIME_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {REGIME_PATH}")

    df = pd.read_csv(REGIME_PATH)

    if df.empty:
        raise ValueError(f"CSV file is empty: {REGIME_PATH}")

    latest_data = df.iloc[-1]

    timestamp = latest_data["Timestamp"]
    regime = latest_data.get("Regime_V2", "Unknown")
    liquidity = float(latest_data.get("Real_Liquidity", 0.0))
    vix = float(latest_data.get("VIX_Index", 0.0))
    ml_veto = _to_bool(latest_data.get("ML_Crash_Veto", False))
    strategy_val = float(latest_data.get("Strategy_Value", 100.0))

    return timestamp, regime, liquidity, vix, ml_veto, strategy_val


def push_latest_prediction_to_db() -> None:
    print("--- Initializing Sentinel Database Engine ---")

    if not DB_URL:
        print("[ERROR] SUPABASE_DB_URL not found in .env file.")
        return

    try:
        timestamp, regime, liquidity, vix, ml_veto, strategy_val = _load_latest_prediction()
        print(f"[INFO] Preparing to push {timestamp} | Regime: {regime}")
    except Exception as e:
        print(f"[ERROR] Failed to load local data: {e}")
        return

    insert_query = f"""
        INSERT INTO {TARGET_TABLE}
        (timestamp, regime_v2, real_liquidity, vix_index, ml_crash_veto, strategy_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (timestamp) DO NOTHING;
    """

    try:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    (timestamp, regime, liquidity, vix, ml_veto, strategy_val),
                )
            conn.commit()

        print("[SUCCESS] Data successfully committed to Supabase Cloud Database!")

    except Exception as e:
        print(f"[ERROR] Database connection or insertion failed: {e}")


if __name__ == "__main__":
    push_latest_prediction_to_db()