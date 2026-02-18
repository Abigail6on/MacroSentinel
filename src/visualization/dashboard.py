import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import numpy as np

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
# We need to re-calculate performance to get attribution, or use the backtest results if they have component returns
# Let's use the backtest results directly if available, otherwise recalculate
BACKTEST_RESULTS = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "performance_dashboard.png")

# Tactical Exposure Map (Must match performance_engine.py)
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks (Overbought - Trim)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Goldilocks (Oversold - Opportunity)": {"QQQ": 0.7, "SPY": 0.3},
    "Neutral / Transitioning": {"SHY": 0.8, "GLD": 0.2},
    "Liquidity Crunch (Defensive)": {"SHY": 1.0} # Future Phase D
}

COLORS = {
    'background': '#ffffff',
    'text': '#2c3e50',
    'grid': '#ecf0f1',
    'strategy': '#16a085', # Teal
    'benchmark': '#95a5a6', # Grey
    'positive': '#27ae60', # Green
    'negative': '#c0392b', # Red
    'gold': '#f1c40f',
    'tech': '#3498db',
    'bonds': '#9b59b6',
    'spy': '#34495e'
}

def create_performance_dashboard():
    if not os.path.exists(BACKTEST_RESULTS):
        print("[ERROR] Backtest results missing. Run performance_engine.py first.")
        return

    # 1. Load Data
    df = pd.read_csv(BACKTEST_RESULTS)
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp')

    # 2. Calculate P&L Attribution (The "Why")
    # We need to reconstruct the daily contribution of each asset
    # This is an approximation based on the Regime column in the backtest file
    assets = ['QQQ', 'SPY', 'GLD', 'SHY']
    contrib_data = {a: [] for a in assets}
    
    for i in range(len(df)):
        regime = df['Regime_V2'].iloc[i]
        weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        
        for asset in assets:
            # Weight * Asset Return = Contribution
            w = weights.get(asset, 0)
            r = df[f"{asset}_Ret"].iloc[i] if f"{asset}_Ret" in df.columns else 0
            # Handle NaN returns (start of series)
            if pd.isna(r): r = 0
            contrib_data[asset].append(w * r)

    # Create DataFrame for contributions
    contrib_df = pd.DataFrame(contrib_data, index=df['Timestamp'])
    total_contrib = contrib_df.sum().sort_values()

    # 3. Setup Plot
    plt.style.use('default')
    fig = plt.figure(figsize=(16, 12))
    fig.patch.set_facecolor(COLORS['background'])
    gs = fig.add_gridspec(3, 2)

    # --- CHART 1: EQUITY CURVE (Top Full Width) ---
    ax1 = fig.add_subplot(gs[0, :])
    
    # Calculate Percentage Return for labels
    strat_ret = (df['Strategy_Value'].iloc[-1] - 1) * 100
    bench_ret = (df['Benchmark_Value'].iloc[-1] - 1) * 100
    
    ax1.plot(df['Timestamp'], df['Strategy_Value'], color=COLORS['strategy'], lw=3, label=f'Strategy ({strat_ret:.2f}%)')
    ax1.plot(df['Timestamp'], df['Benchmark_Value'], color=COLORS['benchmark'], lw=2, ls='--', label=f'S&P 500 ({bench_ret:.2f}%)')
    
    # Fill area between lines
    ax1.fill_between(df['Timestamp'], df['Strategy_Value'], df['Benchmark_Value'], 
                     where=(df['Strategy_Value'] >= df['Benchmark_Value']), color=COLORS['positive'], alpha=0.1)
    ax1.fill_between(df['Timestamp'], df['Strategy_Value'], df['Benchmark_Value'], 
                     where=(df['Strategy_Value'] < df['Benchmark_Value']), color=COLORS['negative'], alpha=0.1)

    ax1.set_title("Total Return Comparison", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax1.legend(loc='upper left')
    ax1.grid(True, color=COLORS['grid'])

    # --- CHART 2: PROFIT DRIVERS (Bottom Left) ---
    ax2 = fig.add_subplot(gs[1:, 0])
    
    # Bar Chart of Total Contribution
    y_pos = np.arange(len(assets))
    # Match colors to asset types
    bar_colors = [COLORS['gold'] if 'GLD' in x else COLORS['tech'] if 'QQQ' in x else COLORS['bonds'] if 'SHY' in x else COLORS['spy'] for x in total_contrib.index]
    
    bars = ax2.barh(y_pos, total_contrib.values * 100, color=bar_colors)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(total_contrib.index, fontsize=12, fontweight='bold')
    ax2.axvline(0, color='black', lw=1)
    
    # Add value labels
    for i, v in enumerate(total_contrib.values * 100):
        ax2.text(v, i, f" {v:.2f}%", va='center', fontweight='bold', color=COLORS['text'])

    ax2.set_title("P&L Attribution: What made money?", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax2.set_xlabel("Contribution to Total Return (%)")
    ax2.grid(True, axis='x', color=COLORS['grid'])

    # --- CHART 3: DRAWDOWN (Bottom Right) ---
    ax3 = fig.add_subplot(gs[1:, 1])
    
    # Calculate Drawdown
    strat_dd = (df['Strategy_Value'] / df['Strategy_Value'].cummax() - 1) * 100
    bench_dd = (df['Benchmark_Value'] / df['Benchmark_Value'].cummax() - 1) * 100
    
    ax3.fill_between(df['Timestamp'], strat_dd, 0, color=COLORS['strategy'], alpha=0.3, label='Strategy Drawdown')
    ax3.plot(df['Timestamp'], bench_dd, color=COLORS['benchmark'], lw=1, ls='--', label='S&P 500 Drawdown')
    
    ax3.set_title("Risk Profile: Drawdown Depth", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax3.set_ylabel("Drawdown (%)")
    ax3.legend(loc='lower left')
    ax3.grid(True, color=COLORS['grid'])

    # Formatting Dates
    for ax in [ax1, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(colors=COLORS['text'], rotation=30)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['grid'])

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART, dpi=100)
    print(f"[SUCCESS] Performance Dashboard saved to {OUTPUT_CHART}")

if __name__ == "__main__":
    create_performance_dashboard()