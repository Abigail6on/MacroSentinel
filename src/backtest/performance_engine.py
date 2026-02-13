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

# --- PHASE A PARAMETERS ---
FRICTION_COST = 0.0002       # 0.02% (2 bps) cost per regime change
MAX_QQQ_WEIGHT = 0.50        
MIN_QQQ_WEIGHT = 0.10        
SENTIMENT_SENSITIVITY = 1.5  

STRATEGY_MAP = {
    "Goldilocks (Growth)": {"QQQ": 0.5, "SPY": 0.3, "GLD": 0.2},
    "Goldilocks -> Tightening (Warning)": {"QQQ": 0.2, "SPY": 0.2, "GLD": 0.4, "SHY": 0.2},
    "Stagflation (High Risk)": {"GLD": 0.6, "DBC": 0.2, "SHY": 0.2},
    "Deflationary Recession": {"TLT": 0.6, "SHY": 0.4},
    "Neutral / Transitioning": {"SPY": 0.5, "SHY": 0.5},
    "Overheat (Inflationary)": {"XLE": 0.4, "DBC": 0.3, "GLD": 0.3}
}

REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",
    "Goldilocks -> Tightening (Warning)": "#f1c40f",
    "Neutral / Transitioning": "#bdc3c7",
    "Stagflation (High Risk)": "#e67e22",
    "Deflationary Recession": "#e74c3c"
}

def run_backtest():
    print("[INFO] Running High-Fidelity Performance Engine...")
    
    if not os.path.exists(REGIME_DATA): return

    # 1. Load & Standardize Precision (Fixes the MergeError)
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.tz_localize(None).astype('datetime64[ns]')
    df = df.sort_values('Timestamp').set_index('Timestamp').resample('h').last().ffill().reset_index()

    # 2. Fetch & Shift Market Returns
    all_tickers = ["SPY", "QQQ", "GLD", "TLT", "DBC", "XLE", "SHY"]
    start_date = (df['Timestamp'].min() - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
    prices = yf.download(all_tickers, start=start_date, interval="1h")['Close']
    prices.index = pd.to_datetime(prices.index).tz_localize(None).astype('datetime64[ns]')
    
    returns = prices.pct_change()
    for t in all_tickers:
        if t in returns.columns: returns[t] = returns[t].shift(-1) # The "Time Machine" fix

    # 3. Align Data
    merged = pd.merge_asof(df.sort_values('Timestamp'), returns.sort_index(), 
                          left_on='Timestamp', right_index=True, direction='backward')
    merged = merged[merged['Timestamp'].dt.hour.between(9, 16)].dropna(subset=['SPY'])

    # 4. Math: Dynamic Scaling + Friction
    strat_rets = []
    prev_regime = None
    trade_count = 0

    for _, row in merged.iterrows():
        regime = row['Regime_V2']
        
        # Scaling Logic
        labor = row.get('Labor_Market', 0)
        mfg = row.get('Manufacturing', 0)
        confidence = np.clip(((labor * 0.6) + (mfg * 0.4)) * SENTIMENT_SENSITIVITY, 0, 1)

        if regime == "Goldilocks (Growth)":
            qqq_w = MIN_QQQ_WEIGHT + (confidence * (MAX_QQQ_WEIGHT - MIN_QQQ_WEIGHT))
            weights = {"QQQ": qqq_w, "SPY": 0.8 - qqq_w, "GLD": 0.2}
        else:
            weights = STRATEGY_MAP.get(regime, STRATEGY_MAP["Neutral / Transitioning"])
        
        h_ret = sum(row[t] * w for t, w in weights.items() if t in row and pd.notnull(row[t]))
        
        if prev_regime and regime != prev_regime:
            h_ret -= FRICTION_COST
            trade_count += 1
            
        strat_rets.append(h_ret)
        prev_regime = regime

    merged['Strategy_Return'] = strat_rets
    merged['Strategy_Value'] = (1 + merged['Strategy_Return']).cumprod()
    merged['Benchmark_Value'] = (1 + merged['SPY']).cumprod()
    merged['Alpha_Basis'] = (merged['Strategy_Value'] - merged['Benchmark_Value']) * 100

    # 5. Risk Metrics (Now fully used)
    merged['Peak'] = merged['Strategy_Value'].cummax()
    max_dd = ((merged['Strategy_Value'] / merged['Peak']) - 1).min() * 100
    vol = merged['Strategy_Return'].std() * np.sqrt(252 * 6.5) * 100
    final_alpha = merged['Alpha_Basis'].iloc[-1]

    # 6. Visualization
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # Top Panel
    ax1.plot(merged['Timestamp'], merged['Strategy_Value'], label='Macro Sentinel (Dynamic)', lw=4, color='#2c3e50')
    ax1.plot(merged['Timestamp'], merged['Benchmark_Value'], label='S&P 500', lw=2, ls='--', color='#bdc3c7')
    
    # NEW: Volatility is now integrated into the Title
    ax1.set_title(f"Alpha: {final_alpha:.4f}% | Max DD: {max_dd:.2f}% | Vol: {vol:.1f}%", 
                  fontsize=18, fontweight='bold', pad=20)
    
    for i in range(len(merged)-1):
        ax1.axvspan(merged['Timestamp'].iloc[i], merged['Timestamp'].iloc[i+1], 
                    color=REGIME_COLORS.get(merged['Regime_V2'].iloc[i], "#fff"), alpha=0.15, lw=0)

    # Bottom Panel
    ax2.fill_between(merged['Timestamp'], merged['Alpha_Basis'], color='#2ecc71', alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))

    plt.tight_layout()
    plt.savefig(PERFORMANCE_CHART, dpi=180)
    merged.to_csv(PERFORMANCE_REPORT, index=False)
    print(f"[SUCCESS] Final Alpha: {final_alpha:.4f}% | Vol: {vol:.2f}%")

if __name__ == "__main__":
    run_backtest()