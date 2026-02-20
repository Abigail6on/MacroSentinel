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
    if len(returns_window) < 10:
        return {"QQQ": 0.6, "SPY": 0.4} # Fallback if not enough data
        
    cov_matrix = returns_window.cov().values
    
    def portfolio_variance(w):
        return np.dot(w.T, np.dot(cov_matrix, w))

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(len(assets)))
    init_guess = [1.0/len(assets)] * len(assets)

    opt = minimize(portfolio_variance, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if opt.success:
        return dict(zip(assets, np.round(opt.x, 2)))
    return {"QQQ": 0.6, "SPY": 0.4}

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): 
        print("[ERROR] Regime data not found.")
        return
        
    df = pd.read_csv(REGIME_DATA)
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').reset_index(drop=True)
    
    tickers = ["QQQ", "SPY", "GLD", "SHY", "XLF", "XLU"]
    
    # Calculate base unshifted returns for the optimizer's historical window
    historical_returns = df[tickers].pct_change()
    
    # Calculate shifted (-1) returns for the actual strategy execution
    for t in tickers:
        if t in df.columns:
            df[f"{t}_Ret"] = df[t].pct_change().shift(-1)

    strat_rets = []
    circuit_breaker_flags = []
    last_regime = None
    
    current_strategy_value = 1.0
    high_water_mark = 1.0
    
    for i in range(len(df)):
        if i == len(df) - 1:
            strat_rets.append(0)
            circuit_breaker_flags.append(False)
            break
            
        row = df.iloc[i]
        regime = row['Regime_V2']
        vix = row['VIX_Index']
        
        # --- CIRCUIT BREAKER ---
        current_drawdown = (high_water_mark - current_strategy_value) / high_water_mark
        is_circuit_breaker_active = current_drawdown >= MAX_DRAWDOWN_LIMIT
        
        if is_circuit_breaker_active:
            final_weights = {"SHY": 1.0}
        else:
            # --- WALK-FORWARD OPTIMIZATION ---
            if regime == "Goldilocks (Growth)":
                if i >= 30:
                    # Look strictly BACKWARDS at the last 30 hours
                    window_rets = historical_returns.iloc[i-30:i+1][["QQQ", "SPY", "XLF", "XLU"]].dropna()
                    weights = get_rolling_optimal_weights(window_rets, ["QQQ", "SPY", "XLF", "XLU"])
                else:
                    weights = {"QQQ": 0.60, "SPY": 0.40} # Burn-in period
            elif regime == "Goldilocks (Overbought - Trim)":
                weights = {"QQQ": 0.2, "SPY": 0.2, "SHY": 0.6}
            elif regime == "Goldilocks (Oversold - Opportunity)":
                weights = {"QQQ": 0.7, "SPY": 0.3}
            else:
                weights = {"SHY": 1.0}

            # Apply VIX Governor
            final_weights = weights.copy()
            if vix > VIX_THRESHOLD:
                equity_list = ["QQQ", "SPY", "XLF", "XLU"]
                reduction_pool = 0
                for t, w in weights.items():
                    if t in equity_list:
                        final_weights[t] = w * 0.5
                        reduction_pool += (w * 0.5)
                final_weights["SHY"] = final_weights.get("SHY", 0) + reduction_pool

        # 3. Execution (Apply calculated weights to the NEXT hour's return)
        hourly_ret = sum(df[f"{k}_Ret"].iloc[i] * v for k, v in final_weights.items() if f"{k}_Ret" in df.columns)
        
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_rets.append(hourly_ret)
        circuit_breaker_flags.append(is_circuit_breaker_active)
        last_regime = regime
        
        current_strategy_value *= (1 + hourly_ret)
        high_water_mark = max(high_water_mark, current_strategy_value)

    # 4. Finalize Metrics
    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100
    df['Circuit_Breaker_Active'] = circuit_breaker_flags

    df.to_csv(PERFORMANCE_REPORT, index=False)
    
    print(f"[SUCCESS] Walk-Forward Optimization Complete.")
    print(f"          Final Alpha (Out-of-Sample): {df['Alpha_Basis'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_performance_engine()