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

# Strategy Allocation Weights
STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks -> Tightening (Warning)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Stagflation (High Risk)": {"GLD": 0.6, "DBC": 0.2, "SHY": 0.2},
    "Deflationary Recession": {"TLT": 0.6, "SHY": 0.4},
    "Neutral / Transitioning": {"SPY": 0.5, "SHY": 0.5},
    "Overheat (Inflationary)": {"XLE": 0.4, "DBC": 0.3, "GLD": 0.3}
}

# Visualization Colors
REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",
    "Goldilocks -> Tightening (Warning)": "#f1c40f",
    "Neutral / Transitioning": "#bdc3c7",
    "Stagflation (High Risk)": "#e67e22",
    "Deflationary Recession": "#e74c3c"
}

def run_backtest():
    print("[INFO] Initializing Real-Time Performance Health Check...")
    
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] No regime history found.")
        return

    # 1. Load Regime History (Timezone-Agnostic)
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None).astype('datetime64[ns]')
    
    # Resample to hourly to collapse multiple bot runs into clean buckets
    df = df.sort_values('Timestamp').set_index('Timestamp').resample('h').last().ffill().reset_index()

    # 2. Fetch Market Data
    all_tickers = ["SPY", "QQQ", "GLD", "TLT", "DBC", "XLE", "SHY"]
    start_date = (df['Timestamp'].min() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"[INFO] Syncing market prices for {all_tickers}...")
    prices = yf.download(all_tickers, start=start_date, interval="1h")['Close']
    
    if prices.empty:
        print("[ERROR] Market data download failed.")
        return

    prices.index = pd.to_datetime(prices.index).tz_localize(None).astype('datetime64[ns]')
    returns = prices.pct_change()

    # 3. Fuzzy Merge and Truth-Testing (Shift Returns)
    # merged = pd.merge_asof(df.sort_values('Timestamp'), 
    #                       returns.sort_index(), 
    #                       left_on='Timestamp', 
    #                       right_index=True, 
    #                       direction='backward')

    # Shift returns forward: Today's signal earns tomorrow's return (Removes Look-ahead Bias)
    for ticker in all_tickers:
        if ticker in returns.columns:
            returns[ticker] = returns[ticker].shift(-1)

    merged = pd.merge_asof(df.sort_values('Timestamp'), 
                          returns.sort_index(), 
                          left_on='Timestamp', 
                          right_index=True, 
                          direction='backward')

    # 4. Filter for US Market Trading Hours (Ottawa/NY Time)
    merged = merged[merged['Timestamp'].dt.hour.between(9, 16)]
    merged = merged.dropna(subset=['SPY'])

    # 5. Performance Math
    strat_rets = []
    for _, row in merged.iterrows():
        regime = row['Regime_V2']
        weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        h_ret = sum(row[t] * w for t, w in weights.items() if t in row and pd.notnull(row[t]))
        strat_rets.append(h_ret)

    merged['Strategy_Return'] = strat_rets
    merged['Benchmark_Return'] = merged['SPY']
    merged['Strategy_Value'] = (1 + merged['Strategy_Return']).cumprod()
    merged['Benchmark_Value'] = (1 + merged['Benchmark_Return']).cumprod()
    merged['Alpha_Basis'] = (merged['Strategy_Value'] - merged['Benchmark_Value']) * 100

    # 6. Health Check Metrics (Risk Analysis)
    # Max Drawdown
    merged['Peak'] = merged['Strategy_Value'].cummax()
    merged['Drawdown'] = (merged['Strategy_Value'] / merged['Peak']) - 1
    max_dd = merged['Drawdown'].min() * 100

    # Volatility
    vol = merged['Strategy_Return'].std() * np.sqrt(252 * 6.5) * 100

    # Capture latest point for reporting (Captured Bloomberg Plunge)
    final_alpha = merged['Alpha_Basis'].iloc[-1]

    # Save Results (PERFORMANCE_REPORT)
    merged.to_csv(PERFORMANCE_REPORT, index=False)

    # 7. High-Fidelity Visualization
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # TOP PANEL: Equity Curve + Shading
    ax1.plot(merged['Timestamp'], merged['Strategy_Value'], label='Macro Sentinel (Strategy)', lw=4, color='#2c3e50', zorder=5)
    ax1.plot(merged['Timestamp'], merged['Benchmark_Value'], label='S&P 500 (Benchmark)', lw=2, ls='--', color='#bdc3c7', zorder=4)
    
    # Add Regime Background Shading
    for i in range(len(merged)-1):
        regime = merged['Regime_V2'].iloc[i]
        color = REGIME_COLORS.get(regime, "#ffffff")
        ax1.axvspan(merged['Timestamp'].iloc[i], merged['Timestamp'].iloc[i+1], color=color, alpha=0.15, lw=0)

    ax1.set_title(f"Cumulative Alpha: {final_alpha:.4f}% | Max DD: {max_dd:.2f}%", fontsize=20, fontweight='bold', pad=20)
    ax1.set_ylabel("Portfolio Growth ($1 Initial)", fontsize=14)
    ax1.legend(loc='upper left', frameon=True, fontsize=12)

    # BOTTOM PANEL: Alpha Spread (The Edge)
    ax2.fill_between(merged['Timestamp'], merged['Alpha_Basis'], color='#2ecc71', alpha=0.3)
    ax2.plot(merged['Timestamp'], merged['Alpha_Basis'], color='#27ae60', lw=2)
    ax2.axhline(0, color='black', lw=1, ls='-')
    ax2.set_ylabel("Alpha (Basis Points)", fontsize=14)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))

    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART, dpi=180)

    print(f"\n--- PERFORMANCE HEALTH CHECK ---")
    print(f"Final Alpha: {final_alpha:.4f}%")
    print(f"Max Drawdown: {max_dd:.4f}% (Peak-to-Trough Pain)")
    print(f"Annualized Vol: {vol:.2f}%")
    print(f"Status: Trading session sync complete.")
    print(f"--------------------------------\n")

if __name__ == "__main__":
    run_backtest()