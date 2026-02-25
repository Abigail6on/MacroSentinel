import pandas as pd
import numpy as np
import os
from scipy.optimize import minimize

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")

# Constants
VIX_THRESHOLD = 20.0
FRICTION_COST = 0.0002 
MAX_DRAWDOWN_LIMIT = 0.05

def get_rolling_optimal_weights(returns_window, assets):
    """Calculates Minimum Variance weights using a localized historical window."""
    available_assets = [a for a in assets if a in returns_window.columns]
    
    if len(returns_window) < 10 or not available_assets:
        return {a: 1.0/max(1, len(available_assets)) for a in available_assets} if available_assets else {"SHY": 1.0}
        
    cov_matrix = returns_window[available_assets].cov().values
    
    def portfolio_variance(w):
        return np.dot(w.T, np.dot(cov_matrix, w))

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # UPGRADE: 40% Cap Rule applied to the backtest to match the live optimizer
    bounds = tuple((0.0, 0.40) for _ in range(len(available_assets)))
    init_guess = [1.0/len(available_assets)] * len(available_assets)

    opt = minimize(portfolio_variance, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if not opt.success:
        return {a: 1.0/len(available_assets) for a in available_assets}
        
    return {available_assets[i]: round(opt.x[i], 4) for i in range(len(available_assets))}

def calculate_backtest():
    print("--- Initializing Sentinel Pro Backtest Engine ---")
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] Regime Data Missing.")
        return

    df = pd.read_csv(REGIME_DATA)
    
    # UPGRADE: Master Global Macro Universe
    assets = ["SPY", "QQQ", "GLD", "SHY", "XLF", "XLU", "XLE", "TLT", "DBC", "EFA", "EEM"]
    
    # 1. Generate T+1 Returns safely for all global assets
    for asset in assets:
        if asset in df.columns:
            df[f"{asset}_Ret"] = df[asset].pct_change().shift(-1).fillna(0)

    strat_rets = []
    circuit_breaker_flags = []
    last_regime = None
    current_strategy_value = 1.0
    high_water_mark = 1.0

    for i in range(len(df)):
        regime = df['Regime_V2'].iloc[i]
        vix = df.get('VIX_Index', pd.Series([0]*len(df))).iloc[i]
        
        is_circuit_breaker_active = False

        # 2. Heuristics & Allocation
        if current_strategy_value < high_water_mark * (1 - MAX_DRAWDOWN_LIMIT):
            weights = {"SHY": 1.0}
            is_circuit_breaker_active = True
        else:
            if regime == "Goldilocks (Growth)":
                if i >= 30:
                    window = df.iloc[i-30:i]
                    # Only feed the risk-on global equities to the optimizer
                    risk_assets = ["SPY", "QQQ", "XLF", "XLU", "XLE", "EFA", "EEM"]
                    ret_window = window[[a for a in risk_assets if a in window.columns]].pct_change().dropna()
                    weights = get_rolling_optimal_weights(ret_window, risk_assets)
                else:
                    weights = {"QQQ": 0.5, "SPY": 0.5}
                    
            # UPGRADE: Syncing the backtest heuristic rules with allocator.py
            elif regime == "Goldilocks (Overbought - Trim)":
                weights = {"SHY": 0.50, "QQQ": 0.25, "SPY": 0.25}
            elif regime == "Goldilocks (Oversold - Opportunity)":
                weights = {"QQQ": 0.60, "SPY": 0.20, "EFA": 0.10, "EEM": 0.10}
            elif regime == "Defensive (Contraction)":
                weights = {"TLT": 0.60, "SHY": 0.40}
            elif regime == "Stagflation / Liquidity Trap":
                weights = {"DBC": 0.50, "GLD": 0.30, "SHY": 0.20}
            else:
                weights = {"SHY": 1.0}

        final_weights = weights.copy()
        
        # 3. Dynamic VIX Risk Management (De-risk all global equities)
        if vix > VIX_THRESHOLD and regime != "Defensive (Contraction)":
            equity_list = ["QQQ", "SPY", "XLF", "XLU", "XLE", "EFA", "EEM"]
            reduction_pool = 0
            for t, w in list(weights.items()):
                if t in equity_list:
                    final_weights[t] = w * 0.5
                    reduction_pool += (w * 0.5)
            final_weights["SHY"] = final_weights.get("SHY", 0) + reduction_pool

        # 4. Execution (Apply calculated weights to the NEXT hour's return)
        hourly_ret = sum(df.get(f"{k}_Ret", pd.Series([0]*len(df))).iloc[i] * v for k, v in final_weights.items())
        
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_rets.append(hourly_ret)
        circuit_breaker_flags.append(is_circuit_breaker_active)
        last_regime = regime
        
        current_strategy_value *= (1 + hourly_ret)
        high_water_mark = max(high_water_mark, current_strategy_value)

    # 5. Finalize Metrics & Build Report Columns Explicitly
    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100
    df['Circuit_Breaker_Active'] = circuit_breaker_flags

    # Explicitly list the exact columns we need for the dashboard and analysis
    base_cols = ['Timestamp', 'Regime_V2', 'Real_Liquidity', 'VIX_Index', 'Strategy_Value', 'Benchmark_Value', 'Alpha_Basis', 'Circuit_Breaker_Active']
    
    # Add whatever asset returns are available
    ret_cols = [f"{a}_Ret" for a in assets if f"{a}_Ret" in df.columns]
    
    # Combine and filter to only what exists in the DataFrame to prevent crashes
    report_cols = base_cols + ret_cols
    available_cols = [c for c in report_cols if c in df.columns]
    
    df[available_cols].to_csv(PERFORMANCE_REPORT, index=False)
    
    final_alpha = df['Alpha_Basis'].iloc[-1]
    print(f"[SUCCESS] Walk-Forward Optimization Complete.")
    print(f"          Final Alpha (Out-of-Sample): {final_alpha:.2f}%")

if __name__ == "__main__":
    calculate_backtest()