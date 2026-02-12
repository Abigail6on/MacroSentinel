import pandas as pd
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

# Strategy Weights
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks -> Tightening (Warning)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Stagflation (High Risk)": {"GLD": 0.6, "DBC": 0.2, "SHY": 0.2},
    "Deflationary Recession": {"TLT": 0.6, "SHY": 0.4},
    "Neutral / Transitioning": {"SPY": 0.5, "SHY": 0.5},
    "Overheat (Inflationary)": {"XLE": 0.4, "DBC": 0.3, "GLD": 0.3}
}

# Match colors with your main dashboard for consistency
REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",
    "Goldilocks -> Tightening (Warning)": "#f1c40f",
    "Neutral / Transitioning": "#95a5a6"
}

def run_backtest():
    print("[INFO] Generating High-Fidelity Performance Chart...")
    
    # 1. Load and Prep Data (Time-Agnostic)
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None)
    df = df.sort_values('Timestamp').set_index('Timestamp').resample('h').last().ffill().reset_index()

    # 2. Fetch Market Data
    all_tickers = ["SPY", "QQQ", "GLD", "TLT", "DBC", "XLE", "SHY"]
    start_date = (df['Timestamp'].min() - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
    prices = yf.download(all_tickers, start=start_date, interval="1h")['Close']
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    returns = prices.pct_change()

    # 3. Fuzzy Merge and Shift
    merged = pd.merge_asof(df.sort_values('Timestamp'), returns.sort_index(), 
                          left_on='Timestamp', right_index=True, direction='backward')
    
    for t in all_tickers:
        if t in merged.columns:
            merged[t] = merged[t].shift(-1)

    # Filter for US Market Hours
    merged = merged[merged['Timestamp'].dt.hour.between(9, 16)]

    # 4. Performance Calculation
    strat_rets = []
    for _, row in merged.iterrows():
        regime = row['Regime_V2']
        weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        strat_rets.append(sum(row[t] * w for t, w in weights.items() if t in row and pd.notnull(row[t])))

    merged['Strategy_Return'] = strat_rets
    merged['Benchmark_Return'] = merged['SPY'].fillna(0)
    merged['Strategy_Value'] = (1 + merged['Strategy_Return']).cumprod()
    merged['Benchmark_Value'] = (1 + merged['Benchmark_Return']).cumprod()
    merged['Alpha_Basis'] = (merged['Strategy_Value'] - merged['Benchmark_Value']) * 100

    # 5. HIGH-FIDELITY VISUALIZATION
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # TOP PANEL: Equity Curve + Shading
    ax1.plot(merged['Timestamp'], merged['Strategy_Value'], label='Macro Sentinel', lw=4, color='#2c3e50', zorder=5)
    ax1.plot(merged['Timestamp'], merged['Benchmark_Value'], label='S&P 500', lw=2, ls='--', color='#bdc3c7', zorder=4)
    
    # Add Regime Shading
    for i in range(len(merged)-1):
        regime = merged['Regime_V2'].iloc[i]
        color = REGIME_COLORS.get(regime, "#ffffff")
        ax1.axvspan(merged['Timestamp'].iloc[i], merged['Timestamp'].iloc[i+1], color=color, alpha=0.15, lw=0)

    ax1.set_title(f"Cumulative Strategy Alpha: {merged['Alpha_Basis'].iloc[-2]:.4f}%", fontsize=20, fontweight='bold', pad=20)
    ax1.set_ylabel("Portfolio Value (Initial=$1.00)", fontsize=14)
    ax1.legend(loc='upper left', frameon=True, fontsize=12)

    # BOTTOM PANEL: Alpha Spread (The "Edge")
    ax2.fill_between(merged['Timestamp'], merged['Alpha_Basis'], color='#2ecc71', alpha=0.3)
    ax2.plot(merged['Timestamp'], merged['Alpha_Basis'], color='#27ae60', lw=2)
    ax2.axhline(0, color='black', lw=1, ls='-')
    ax2.set_ylabel("Alpha (Basis Points)", fontsize=14)
    ax2.set_title("Strategy Edge (Over/Under Benchmark)", fontsize=14, fontweight='semibold')

    # Formatting X-Axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    plt.xticks(rotation=0)

    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART, dpi=180)
    print(f"--- SUCCESS ---")
    print(f"Alpha Generated: {merged['Alpha_Basis'].iloc[-2]:.4f}%")

if __name__ == "__main__":
    run_backtest()