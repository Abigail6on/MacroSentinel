import pandas as pd
import numpy as np
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")

# --- STRATEGY MAP ---
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.6, "SPY": 0.4},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "SHY": 0.6},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    "Neutral / Transitioning": {"SHY": 1.0},
    "Liquidity Crunch (Defensive)": {"SHY": 1.0}
}

# --- STEP 3: THE VOLATILITY GOVERNOR ---
VIX_THRESHOLD = 20.0  # Level where we trigger the "Safety Belt"
FRICTION_COST = 0.0002 

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): 
        print("[ERROR] Regime data not found.")
        return
        
    df = pd.read_csv(REGIME_DATA)
    if 'SPY' not in df.columns or 'VIX_Index' not in df.columns:
        print("[ERROR] Required data columns missing.")
        return

    # 1. Prepare Returns
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp')
    
    tickers = ["QQQ", "SPY", "GLD", "SHY"]
    for t in tickers:
        df[f"{t}_Ret"] = df[t].pct_change()

    # 2. Backtest with Dynamic Governor
    strat_rets = []
    last_regime = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        regime = row['Regime_V2']
        vix = row['VIX_Index']
        
        # Get base weights from the skeleton
        base_weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        final_weights = base_weights.copy()
        
        # APPLY THE GOVERNOR: If VIX is high, cut Equity risk by 50%
        if vix > VIX_THRESHOLD:
            equity_tickers = ['QQQ', 'SPY']
            reduction_pool = 0
            
            for ticker in equity_tickers:
                if ticker in final_weights:
                    original_w = final_weights[ticker]
                    final_weights[ticker] = original_w * 0.5  # Cut in half
                    reduction_pool += (original_w * 0.5)
            
            # Reallocate the "safety" portion into SHY (Cash)
            final_weights['SHY'] = final_weights.get('SHY', 0) + reduction_pool

        # Calculate Returns
        hourly_ret = sum(df[f"{k}_Ret"].iloc[i] * v for k, v in final_weights.items() if f"{k}_Ret" in df.columns)
        
        # Account for trading costs on regime change
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_rets.append(hourly_ret)
        last_regime = regime

    # 3. Finalize Stats
    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100

    df.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Performance Engine updated with VIX Governor. Final Alpha: {df['Alpha_Basis'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_performance_engine()