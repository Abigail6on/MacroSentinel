import pandas as pd
import numpy as np
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")

# Constants
STEEP_THRESHOLD = 0.70  
FLAT_THRESHOLD = 0.40   
VIX_THRESHOLD = 20.0
FRICTION_COST = 0.0002 

# Institutional Risk Management
MAX_DRAWDOWN_LIMIT = 0.05  # 5% maximum allowed drawdown from High-Water Mark

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): 
        print("[ERROR] Regime data not found.")
        return
        
    df = pd.read_csv(REGIME_DATA)
    
    # 1. Data Sanitization
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').reset_index(drop=True)
    
    # 2. Comprehensive Return Calculation
    tickers = ["QQQ", "SPY", "GLD", "SHY", "XLF", "XLU"]
    for t in tickers:
        if t in df.columns:
            df[f"{t}_Ret"] = df[t].pct_change().shift(-1)
        else:
            print(f"[WARNING] Ticker {t} not found in input data.")

    strat_rets = []
    circuit_breaker_flags = []
    last_regime = None
    
    # Live variables for Path-Dependent Stop Loss
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
        yield_curve = row['Yield_Curve_10Y2Y']
        
        # --- CIRCUIT BREAKER CHECK ---
        # Calculate current drawdown from the all-time high
        current_drawdown = (high_water_mark - current_strategy_value) / high_water_mark
        is_circuit_breaker_active = current_drawdown >= MAX_DRAWDOWN_LIMIT
        
        if is_circuit_breaker_active:
            # Emergency Liquidation to 100% Cash
            final_weights = {"SHY": 1.0}
        else:
            # Normal Allocator Logic
            if regime == "Goldilocks (Growth)":
                if yield_curve > STEEP_THRESHOLD:
                    weights = {"QQQ": 0.50, "SPY": 0.30, "XLF": 0.20}
                elif yield_curve < FLAT_THRESHOLD:
                    weights = {"QQQ": 0.50, "SPY": 0.30, "XLU": 0.20}
                else:
                    weights = {"QQQ": 0.60, "SPY": 0.40}
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

        # 3. Calculate Strategy Return
        hourly_ret = sum(df[f"{k}_Ret"].iloc[i] * v for k, v in final_weights.items() if f"{k}_Ret" in df.columns)
        
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_rets.append(hourly_ret)
        circuit_breaker_flags.append(is_circuit_breaker_active)
        last_regime = regime
        
        # 4. Update Path-Dependent Variables for next loop iteration
        current_strategy_value *= (1 + hourly_ret)
        high_water_mark = max(high_water_mark, current_strategy_value)

    # 5. Finalize Metrics
    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100
    df['Circuit_Breaker_Active'] = circuit_breaker_flags

    df.to_csv(PERFORMANCE_REPORT, index=False)
    
    cb_count = sum(circuit_breaker_flags)
    print(f"[SUCCESS] Circuit Breaker evaluated. Triggered {cb_count} times.")
    print(f"          Final Alpha: {df['Alpha_Basis'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    run_performance_engine()