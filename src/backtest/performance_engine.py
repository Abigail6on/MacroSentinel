import pandas as pd
import numpy as np
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")

# Strategy Map - Aligned with allocator.py
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.6, "SPY": 0.4},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "SHY": 0.6},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    "Neutral / Transitioning": {"SHY": 1.0},
    "Liquidity Crunch (Defensive)": {"SHY": 1.0}
}

VIX_THRESHOLD = 20.0
FRICTION_COST = 0.0002 

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): 
        print("[ERROR] Regime data not found.")
        return
        
    df = pd.read_csv(REGIME_DATA)
    if 'SPY' not in df.columns or 'VIX_Index' not in df.columns:
        print("[ERROR] Required data columns missing.")
        return

    # 1. Data Sanitization
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').reset_index(drop=True)
    
    # 2. Return Calculation with Look-Ahead Mitigation
    # We calculate the pct_change for the NEXT interval.
    # This means Return_at_T is the profit/loss between T and T+1.
    tickers = ["QQQ", "SPY", "GLD", "SHY"]
    for t in tickers:
        df[f"{t}_Ret"] = df[t].pct_change().shift(-1) 

    # 3. Execution Simulation
    strat_rets = []
    last_regime = None
    
    for i in range(len(df)):
        # At the very last row, we have no "next" return to calculate, so we break
        if i == len(df) - 1:
            strat_rets.append(0)
            break
            
        row = df.iloc[i]
        regime = row['Regime_V2']
        vix = row['VIX_Index']
        
        # Determine Weights based on current info
        base_weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        final_weights = base_weights.copy()
        
        # Apply VIX Governor
        if vix > VIX_THRESHOLD:
            equity_tickers = ['QQQ', 'SPY']
            reduction_pool = 0
            for ticker in equity_tickers:
                if ticker in final_weights:
                    original_w = final_weights[ticker]
                    final_weights[ticker] = original_w * 0.5
                    reduction_pool += (original_w * 0.5)
            final_weights['SHY'] = final_weights.get('SHY', 0) + reduction_pool

        # Calculate Returns (Apply T weights to T+1 returns)
        hourly_ret = sum(df[f"{k}_Ret"].iloc[i] * v for k, v in final_weights.items() if f"{k}_Ret" in df.columns)
        
        # Transaction Costs (Slippage/Commission)
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_rets.append(hourly_ret)
        last_regime = regime

    # 4. Metric Finalization
    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    # Benchmark also needs to be shifted for an apples-to-apples comparison
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100

    df.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Alpha Integrity Check Complete. Final Alpha: {df['Alpha_Basis'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_performance_engine()