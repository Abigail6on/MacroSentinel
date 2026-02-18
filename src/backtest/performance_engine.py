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

# --- UNIFIED LIGHT PALETTE ---
# Pastel colors for background shading (Light Mode Friendly)
REGIME_COLORS = {
    "Goldilocks (Growth)": "#d5f5e3",           # Pastel Green
    "Goldilocks (Overbought - Trim)": "#fcf3cf", # Pastel Yellow
    "Goldilocks (Oversold - Opportunity)": "#d6eaf8", # Pastel Blue
    "Neutral / Transitioning": "#f2f3f4",       # Light Grey
    "Stagflation (High Risk)": "#fadbd8",       # Pastel Red
    "Deflationary Recession": "#e8daef"         # Pastel Purple
}

COLORS = {
    'background': '#ffffff',
    'text': '#2c3e50',
    'strategy': '#16a085',   # Deep Teal (Matches Dashboard)
    'benchmark': '#7f8c8d',  # Grey
    'alpha_pos': '#27ae60',  # Green
    'alpha_neg': '#c0392b'   # Red
}

STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    "Neutral / Transitioning": {"SHY": 0.8, "GLD": 0.2}
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

    # 3. Visualization (Light Mode)
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    fig.patch.set_facecolor(COLORS['background'])

    # Top Panel: Equity + Shading
    
    ax1.plot(df['Timestamp'], df['Strategy_Value'], label='Macro Sentinel', lw=3, color=COLORS['strategy'])
    ax1.plot(df['Timestamp'], df['Benchmark_Value'], label='S&P 500', lw=2, ls='--', color=COLORS['benchmark'])
    
    # Efficient Shading Logic
    df['regime_group'] = (df['Regime_V2'] != df['Regime_V2'].shift()).cumsum()
    for _, group in df.groupby('regime_group'):
        regime_label = group['Regime_V2'].iloc[0]
        color = REGIME_COLORS.get(regime_label, "#f2f3f4")
        # Use full opacity for pastel colors in light mode
        ax1.axvspan(group['Timestamp'].iloc[0], group['Timestamp'].iloc[-1], color=color, alpha=1.0)

    ax1.set_title(f"Strategy Performance | Alpha: {df['Alpha_Basis'].iloc[-1]:.2f}%", fontsize=16, fontweight='bold', color=COLORS['text'])
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    ax1.grid(True, color='#ecf0f1')

    # Bottom Panel: Alpha Spread
    ax2.fill_between(df['Timestamp'], df['Alpha_Basis'], 0, where=(df['Alpha_Basis'] >= 0), color=COLORS['alpha_pos'], alpha=0.6)
    ax2.fill_between(df['Timestamp'], df['Alpha_Basis'], 0, where=(df['Alpha_Basis'] < 0), color=COLORS['alpha_neg'], alpha=0.6)
    ax2.set_ylabel("Alpha Basis (%)", color=COLORS['text'])
    ax2.grid(True, color='#ecf0f1')

    # Formatting
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45, color=COLORS['text'])
    plt.yticks(color=COLORS['text'])
    
    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART, dpi=100)
    df.drop(columns=['regime_group']).to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Performance Chart (Light Mode) saved to {PERFORMANCE_CHART}")

if __name__ == "__main__":
    run_performance_engine()