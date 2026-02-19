import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# --- PATH CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sentinel_pro_dashboard.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_pro_dashboard():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Backtest results not found at {DATA_PATH}")
        return

    # 1. Load and Clean Data
    df = pd.read_csv(DATA_PATH)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    # 2. Setup Figure
    plt.style.use('fivethirtyeight') # Gives a clean, institutional look
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16), 
                                       gridspec_kw={'height_ratios': [3, 1, 1]})
    fig.patch.set_facecolor('white')

    # --- PLOT 1: PRECISION EQUITY CURVE & REGIMES ---
    ax1.plot(df['Timestamp'], df['Strategy_Value'], label='Macro Sentinel (Strategy)', color='#2E86C1', linewidth=3)
    ax1.plot(df['Timestamp'], df['Benchmark_Value'], label='S&P 500 (Benchmark)', color='#5D6D7E', alpha=0.5, linestyle='--')

    # Color coded Regime Underlays
    regime_colors = {
        'Goldilocks (Growth)': '#D5F5E3',             # Soft Green
        'Neutral / Transitioning': '#F2F3F4',         # Soft Grey
        'Liquidity Crunch (Defensive)': '#FADBD8',    # Soft Red
        'Goldilocks (Overbought - Trim)': '#FCF3CF'   # Soft Yellow
    }

    for regime, color in regime_colors.items():
        mask = df['Regime_V2'] == regime
        if mask.any():
            ax1.fill_between(df['Timestamp'], 0.5, 1.5, where=mask, color=color, alpha=0.5, label=f'Regime: {regime}')

    ax1.set_ylim(df[['Strategy_Value', 'Benchmark_Value']].min().min()*0.98, 1.05)
    ax1.set_title('MacroSentinel: Performance vs. Market Regimes', fontsize=20, fontweight='bold', pad=20)
    ax1.set_ylabel('Normalized Portfolio Value', fontsize=12)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.4)

    # --- PLOT 2: DRAWDOWN (The "Pain" Metric) ---
    rolling_max = df['Strategy_Value'].cummax()
    drawdown = (df['Strategy_Value'] / rolling_max - 1) * 100
    ax2.fill_between(df['Timestamp'], drawdown, 0, color='#E74C3C', alpha=0.3)
    ax2.plot(df['Timestamp'], drawdown, color='#C0392B', linewidth=1.5)
    ax2.set_title('Strategic Drawdown (%) - Measure of Capital Protection', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Loss from Peak %', fontsize=11)
    ax2.set_ylim(drawdown.min()*1.2, 1)
    ax2.grid(True, linestyle='--', alpha=0.4)

    # --- PLOT 3: ALPHA DRIVERS (VIX & LIQUIDITY) ---
    ax3.plot(df['Timestamp'], df['VIX_Index'], color='#8E44AD', label='VIX (Market Volatility)', linewidth=2)
    ax3_twin = ax3.twinx()
    ax3_twin.plot(df['Timestamp'], df['Real_Liquidity'], color='#27AE60', label='Real Liquidity (M2-CPI)', alpha=0.7, linewidth=2)
    
    ax3.set_title('Regime Drivers: Risk (VIX) vs. Fuel (Liquidity)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('VIX Level', color='#8E44AD', fontweight='bold')
    ax3_twin.set_ylabel('Liquidity %', color='#27AE60', fontweight='bold')

    # Merge legends for the twin-axis chart
    lines, labels = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='white')

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE)
    print(f"[SUCCESS] Pro Dashboard saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_pro_dashboard()