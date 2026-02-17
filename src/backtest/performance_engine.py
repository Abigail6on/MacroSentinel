import pandas as pd
import numpy as np
import yfinance as yf
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
PERFORMANCE_CHART = os.path.join(BASE_DIR, "output", "performance_comparison.png")

# --- PHASE A & C PARAMETERS ---
FRICTION_COST = 0.0002       # 0.02% cost per regime change
REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",           # Green
    "Goldilocks (Overbought - Trim)": "#f1c40f", # Yellow (Caution)
    "Goldilocks (Oversold - Opportunity)": "#3498db", # Blue (Buy Dip)
    "Neutral / Transitioning": "#95a5a6",       # Grey
    "Stagflation (High Risk)": "#e74c3c",       # Red
    "Deflationary Recession": "#8e44ad"         # Purple
}

# Updated Strategy Map for Phase C RSI Signals
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3}, # Aggressive 100% Equity
    "Neutral / Transitioning": {"SHY": 0.8, "GLD": 0.2},
    "Stagflation (High Risk)": {"GLD": 0.6, "DBC": 0.2, "SHY": 0.2},
    "Deflationary Recession": {"SHY": 1.0}
}

def run_performance_engine():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] No regime data found.")
        return

    # 1. Load Data
    merged = pd.read_csv(REGIME_DATA)
    
    # --- CRITICAL X-AXIS FIX ---
    merged['Timestamp'] = pd.to_datetime(merged['Timestamp']).dt.tz_localize(None)
    merged = merged.sort_values('Timestamp').dropna(subset=['SPY'])

    # 2. Calculate Returns for all assets
    tickers = ["QQQ", "SPY", "GLD", "SHY", "DBC", "TLT", "XLE"]
    for t in tickers:
        merged[f"{t}_Ret"] = merged[t].pct_change()

    # 3. Backtest Loop
    strat_returns = []
    current_weights = None
    last_regime = None

    for i in range(len(merged)):
        regime = merged['Regime_V2'].iloc[i]
        weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        
        # Calculate hourly return
        hourly_ret = sum(merged[f"{k}_Ret"].iloc[i] * v for k, v in weights.items() if f"{k}_Ret" in merged.columns)
        
        # Apply Friction if regime changed
        if last_regime and regime != last_regime:
            hourly_ret -= FRICTION_COST
            
        strat_returns.append(hourly_ret)
        last_regime = regime

    merged['Strategy_Return'] = strat_returns
    merged['Strategy_Value'] = (1 + merged['Strategy_Return'].fillna(0)).cumprod()
    merged['Benchmark_Value'] = (1 + merged['SPY_Ret'].fillna(0)).cumprod()
    merged['Alpha_Basis'] = (merged['Strategy_Value'] - merged['Benchmark_Value']) * 100

    # 4. Metrics
    merged['Peak'] = merged['Strategy_Value'].cummax()
    max_dd = ((merged['Strategy_Value'] / merged['Peak']) - 1).min() * 100
    vol = merged['Strategy_Return'].std() * np.sqrt(252 * 6.5) * 100
    final_alpha = merged['Alpha_Basis'].iloc[-1]

    # 5. Visualization
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # Top Panel: Equity Curve
    ax1.plot(merged['Timestamp'], merged['Strategy_Value'], label='Macro Sentinel (Tactical)', lw=3, color='#00d1b2')
    ax1.plot(merged['Timestamp'], merged['Benchmark_Value'], label='S&P 500 (SPY)', lw=1.5, ls='--', color='#7f8c8d')
    
    # Shade Regimes
    for i in range(len(merged)-1):
        color = REGIME_COLORS.get(merged['Regime_V2'].iloc[i], "#34495e")
        ax1.axvspan(merged['Timestamp'].iloc[i], merged['Timestamp'].iloc[i+1], color=color, alpha=0.15)

    ax1.set_title(f"Phase C Strategy: Alpha {final_alpha:.2f}% | Vol {vol:.1f}%", fontsize=16, pad=20)
    ax1.legend()

    # Bottom Panel: Alpha Basis
    ax2.fill_between(merged['Timestamp'], merged['Alpha_Basis'], 0, 
                     where=(merged['Alpha_Basis'] >= 0), color='#2ecc71', alpha=0.4)
    ax2.fill_between(merged['Timestamp'], merged['Alpha_Basis'], 0, 
                     where=(merged['Alpha_Basis'] < 0), color='#e74c3c', alpha=0.4)
    ax2.set_ylabel("Alpha Basis (bps)")

    # Formatting X-Axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART)
    merged.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Phase C Performance synced. X-Axis mapped to {merged['Timestamp'].max()}")

if __name__ == "__main__":
    run_performance_engine()