import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

# --- UNIFIED LIGHT PALETTE ---
COLORS = {
    'background': '#ffffff',
    'text': '#2c3e50',       # Dark Slate
    'grid': '#ecf0f1',       # Very Light Grey
    'strategy': '#16a085',   # Deep Teal
    'benchmark': '#95a5a6',  # Grey
    'inflation': '#c0392b',  # Deep Red
    'rsi': '#2980b9',        # Strong Blue
    'growth_pos': '#27ae60', # Emerald
    'growth_neg': '#e74c3c', # Soft Red
    'regime': '#1abc9c'      # Teal Green
}

def create_dashboard():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] Regime data missing.")
        return

    # 1. Load and Sanitize
    df = pd.read_csv(REGIME_DATA)
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.floor('h').dt.tz_localize(None)
    df = df.sort_values('Timestamp')

    # 2. Setup Plot (Light Mode)
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
    fig.patch.set_facecolor(COLORS['background'])
    plt.subplots_adjust(hspace=0.4, wspace=0.2)

    # --- CHART 1: REGIME EVOLUTION ---
    ax1.step(df['Timestamp'], df['Regime_V2'], where='post', color=COLORS['regime'], lw=2.5)
    ax1.set_title("Current Market Regime", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax1.grid(True, color=COLORS['grid'])
    ax1.set_facecolor(COLORS['background'])

    # --- CHART 2: INFLATION BRIDGE ---
    last_inf = df['Inflation_YoY'].iloc[-1]
    ax2.plot(df['Timestamp'], df['Inflation_YoY'], color=COLORS['inflation'], lw=2.5, label='YoY Inflation')
    ax2.axhline(2.0, color='gray', ls='--', alpha=0.5, label='Fed Target (2%)')
    ax2.set_title(f"Inflation: {last_inf:.2f}%", fontsize=14, fontweight='bold', color=COLORS['inflation'])
    ax2.legend(loc='upper left')
    ax2.grid(True, color=COLORS['grid'])

    # --- CHART 3: GROWTH PULSE ---
    growth_pulse = (df['Labor_Market'] * 0.6) + (df['Manufacturing'] * 0.4)
    ax3.fill_between(df['Timestamp'], growth_pulse, 0, where=(growth_pulse >= 0), color=COLORS['growth_pos'], alpha=0.4)
    ax3.fill_between(df['Timestamp'], growth_pulse, 0, where=(growth_pulse < 0), color=COLORS['growth_neg'], alpha=0.4)
    ax3.plot(df['Timestamp'], growth_pulse, color=COLORS['text'], lw=1, alpha=0.6)
    ax3.set_title("Growth Pulse (Economic Health)", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax3.grid(True, color=COLORS['grid'])

    # --- CHART 4: RSI SPEEDOMETER ---
    
    last_rsi = df['RSI'].iloc[-1]
    ax4.plot(df['Timestamp'], df['RSI'], color=COLORS['rsi'], lw=2)
    ax4.axhline(70, color=COLORS['growth_neg'], ls=':', lw=2)
    ax4.axhline(30, color=COLORS['growth_pos'], ls=':', lw=2)
    ax4.set_title(f"SPY RSI: {last_rsi:.1f}", fontsize=14, fontweight='bold', color=COLORS['rsi'])
    ax4.set_ylim(0, 100)
    ax4.grid(True, color=COLORS['grid'])

    # Formatting
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H'))
        ax.tick_params(colors=COLORS['text'], rotation=30)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['grid'])

    plt.savefig(OUTPUT_CHART, dpi=100, bbox_inches='tight')
    print(f"[SUCCESS] Dashboard (Light Mode) saved to {OUTPUT_CHART}")

if __name__ == "__main__":
    create_dashboard()