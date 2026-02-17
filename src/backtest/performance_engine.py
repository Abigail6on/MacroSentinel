import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
PERFORMANCE_CHART = os.path.join(BASE_DIR, "output", "performance_comparison.png")

FRICTION_COST = 0.0002 

# --- VIBRANT COLORS FOR VISIBILITY ---
REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",           # Vibrant Green
    "Goldilocks (Overbought - Trim)": "#f1c40f", # Warning Yellow
    "Goldilocks (Oversold - Opportunity)": "#3498db", # Opportunity Blue
    "Neutral / Transitioning": "#bdc3c7",       # Neutral Grey
    "Stagflation (High Risk)": "#e74c3c",       # Danger Red
    "Deflationary Recession": "#8e44ad"         # Recession Purple
}

STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    "Neutral / Transitioning": {"SHY": 0.8, "GLD": 0.2},
    "Stagflation (High Risk)": {"GLD": 0.6, "DBC": 0.2, "SHY": 0.2},
    "Deflationary Recession": {"SHY": 1.0}
}

def run_performance_engine():
    if not os.path.exists(REGIME_DATA): return

    # 1. Load and Sanitize Data
    df = pd.read_csv(REGIME_DATA)
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').dropna(subset=['SPY'])

    # 2. Returns Calculation
    tickers = ["QQQ", "SPY", "GLD", "SHY", "DBC", "TLT", "XLE"]
    for t in tickers:
        df[f"{t}_Ret"] = df[t].pct_change()

    # 3. Allocation Loop
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

    df['Strategy_Value'] = (1 + pd.Series(strat_rets).fillna(0)).cumprod()
    df['Benchmark_Value'] = (1 + df['SPY_Ret'].fillna(0)).cumprod()
    df['Alpha_Basis'] = (df['Strategy_Value'] - df['Benchmark_Value']) * 100

    # 4. Visualization
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # Top Panel: Equity + THE GREEN AREA (Regime Shading)
    ax1.plot(df['Timestamp'], df['Strategy_Value'], label='Macro Sentinel', lw=3, color='#00d1b2')
    ax1.plot(df['Timestamp'], df['Benchmark_Value'], label='S&P 500', lw=1, ls='--', color='white', alpha=0.5)
    
    # --- SHADING LOGIC FIX ---
    # We iterate through each hour and paint the background the regime color
    for i in range(len(df)-1):
        regime_label = df['Regime_V2'].iloc[i]
        color = REGIME_COLORS.get(regime_label, "#34495e")
        ax1.axvspan(df['Timestamp'].iloc[i], df['Timestamp'].iloc[i+1], color=color, alpha=0.2)

    ax1.set_title("Strategy Performance & Regime Context", fontsize=16, pad=20)
    ax1.legend(loc='upper left')

    # Bottom Panel: Alpha Spread
    ax2.fill_between(df['Timestamp'], df['Alpha_Basis'], 0, where=(df['Alpha_Basis'] >= 0), color='#2ecc71', alpha=0.5)
    ax2.fill_between(df['Timestamp'], df['Alpha_Basis'], 0, where=(df['Alpha_Basis'] < 0), color='#e74c3c', alpha=0.5)
    ax2.set_ylabel("Alpha Basis (bps)")

    # X-Axis Formatting
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART)
    df.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Performance Chart updated with Regime Shading.")

if __name__ == "__main__":
    run_performance_engine()