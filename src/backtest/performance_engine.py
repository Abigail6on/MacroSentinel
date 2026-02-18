import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt # Kept only for internal calc, no plotting needed

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")

# --- THE FIX: CASH IS KING ---
# We removed Gold (GLD) from defensive modes.
STRATEGY_MAP = {
    # Bull Market (Aggressive)
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "SHY": 0.6}, # Moved to Cash, not Gold
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    
    # Bear/Chop (Safety)
    "Neutral / Transitioning": {"SHY": 1.0},        # 100% Cash. No Gold risk.
    "Liquidity Crunch (Defensive)": {"SHY": 1.0}    # 100% Cash.
}

FRICTION_COST = 0.0002 

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): return
    df = pd.read_csv(REGIME_DATA)
    if 'SPY' not in df.columns: return

    # 1. Sanitize
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').dropna(subset=['SPY'])

    # 2. Backtest
    tickers = ["QQQ", "SPY", "GLD", "SHY"]
    for t in tickers:
        df[f"{t}_Ret"] = df[t].pct_change()

    strat_rets = []
    last_regime = None
    for i in range(len(df)):
        regime = df['Regime_V2'].iloc[i]
        weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        
        hourly_ret = sum(df[f"{k}_Ret"].iloc[i] * v for k, v in weights.items() if f"{k}_Ret" in df.columns)
        
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
        strat_rets.append(hourly_ret)
        last_regime = regime

    df['Strategy_Value'] = (1 + pd.Series(strat_rets, index=df.index).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100

    # Save Results
    df.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Strategy Updated. Gold removed from Defense. New Alpha: {df['Alpha_Basis'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_performance_engine()