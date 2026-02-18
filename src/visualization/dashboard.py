import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Path Management
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_dashboard_v2.png")

def create_dashboard():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] Regime data missing.")
        return

    # 1. Load and Sanitize
    df = pd.read_csv(REGIME_DATA)
    
    # --- CRITICAL TIMELINE FIX ---
    # We strip the milliseconds to ensure the X-axis can group the hours correctly
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.floor('h').dt.tz_localize(None)
    df = df.sort_values('Timestamp')

    # 2. Setup Plot
    plt.style.use('dark_background')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
    plt.subplots_adjust(hspace=0.3, wspace=0.2)

    # --- CHART 1: REGIME EVOLUTION ---
    ax1.step(df['Timestamp'], df['Regime_V2'], where='post', color='#00d1b2', lw=2)
    ax1.set_title("Current Market Regime (Phase C)", fontsize=14, color='#00d1b2')
    ax1.tick_params(axis='x', rotation=30)

    # --- CHART 2: INFLATION BRIDGE (The Fix) ---
    # 
    ax2.plot(df['Timestamp'], df['Inflation_YoY'], color='#ff4757', lw=3, label='YoY Inflation %')
    ax2.axhline(2.0, color='white', ls='--', alpha=0.5, label='Fed Target')
    ax2.set_title(f"Inflation Percentage: {df['Inflation_YoY'].iloc[-1]:.2f}%", fontsize=14, color='#ff4757')
    ax2.legend()

    # --- CHART 3: GROWTH PULSE (Labor + Manufacturing) ---
    growth_pulse = (df['Labor_Market'] * 0.6) + (df['Manufacturing'] * 0.4)
    ax3.fill_between(df['Timestamp'], growth_pulse, 0, where=(growth_pulse >= 0), color='#2ecc71', alpha=0.3)
    ax3.fill_between(df['Timestamp'], growth_pulse, 0, where=(growth_pulse < 0), color='#ff4757', alpha=0.3)
    ax3.plot(df['Timestamp'], growth_pulse, color='white', lw=1, alpha=0.8)
    ax3.set_title("Growth Pulse (Economic Health)", fontsize=14)

    # --- CHART 4: RSI SPEEDOMETER ---
    # 
    ax4.plot(df['Timestamp'], df['RSI'], color='#3498db', lw=2)
    ax4.axhline(70, color='#e74c3c', ls=':', alpha=0.5) # Overbought
    ax4.axhline(30, color='#2ecc71', ls=':', alpha=0.5) # Oversold
    ax4.set_title(f"SPY RSI: {df['RSI'].iloc[-1]:.1f}", fontsize=14, color='#3498db')

    # Global Date Formatting
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.grid(alpha=0.1)

    plt.savefig(OUTPUT_CHART)
    print(f"[SUCCESS] Dashboard updated. Inflation now tracking at {df['Inflation_YoY'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    create_dashboard()