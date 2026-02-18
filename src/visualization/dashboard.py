import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import numpy as np

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

# --- UNIFIED LIGHT PALETTE ---
COLORS = {
    'background': '#ffffff',
    'text': '#2c3e50',
    'grid': '#ecf0f1',
    'strategy': '#16a085',
    'inflation': '#c0392b',
    'rsi': '#2980b9',
    'labor': '#2ecc71',      # Bright Green for Labor
    'mfg': '#9b59b6',        # Purple for Manufacturing
    'pulse': '#2c3e50',      # Dark Slate for the Net Pulse Line
    'threshold': '#f39c12',  # Orange for the "Goldilocks Line"
    'regime': '#1abc9c',
    'growth_pos': '#27ae60',
    'growth_neg': '#e74c3c'
}

def create_dashboard():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] Regime data missing.")
        return

    # 1. Load and Sanitize
    df = pd.read_csv(REGIME_DATA)
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.floor('h').dt.tz_localize(None)
    df = df.sort_values('Timestamp')

    # 2. Setup Plot
    plt.style.use('default')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
    fig.patch.set_facecolor(COLORS['background'])
    plt.subplots_adjust(hspace=0.4, wspace=0.2)

    # --- CHART 1: REGIME EVOLUTION ---
    ax1.step(df['Timestamp'], df['Regime_V2'], where='post', color=COLORS['regime'], lw=2.5)
    ax1.set_title("Current Market Regime", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax1.grid(True, color=COLORS['grid'])

    # --- CHART 2: INFLATION BRIDGE ---
    last_inf = df['Inflation_YoY'].iloc[-1]
    ax2.plot(df['Timestamp'], df['Inflation_YoY'], color=COLORS['inflation'], lw=2.5, label='YoY Inflation')
    ax2.axhline(2.0, color='gray', ls='--', alpha=0.5, label='Fed Target')
    ax2.set_title(f"Inflation: {last_inf:.2f}%", fontsize=14, fontweight='bold', color=COLORS['inflation'])
    ax2.legend(loc='upper left')
    ax2.grid(True, color=COLORS['grid'])

    # --- CHART 3: THE GROWTH ATTRIBUTION (New "Readable" Logic) ---
    # We split the pulse into its "Weighted Components"
    w_labor = df['Labor_Market'] * 0.6
    w_mfg = df['Manufacturing'] * 0.4
    net_pulse = w_labor + w_mfg

    # Separate Positive and Negative contributions for Stacking
    # This effectively creates a "Stacked Bar" look using area fills
    pos_labor = w_labor.clip(lower=0)
    neg_labor = w_labor.clip(upper=0)
    pos_mfg = w_mfg.clip(lower=0)
    neg_mfg = w_mfg.clip(upper=0)

    # Stack the Positive Areas (Green base, Purple on top)
    ax3.fill_between(df['Timestamp'], 0, pos_labor, color=COLORS['labor'], alpha=0.6, label='Labor Contrib (+)')
    ax3.fill_between(df['Timestamp'], pos_labor, pos_labor + pos_mfg, color=COLORS['mfg'], alpha=0.6, label='Mfg Contrib (+)')

    # Stack the Negative Areas (Green base down, Purple below that)
    ax3.fill_between(df['Timestamp'], 0, neg_labor, color=COLORS['labor'], alpha=0.3) # Fainter green for negative
    ax3.fill_between(df['Timestamp'], neg_labor, neg_labor + neg_mfg, color=COLORS['mfg'], alpha=0.3) # Fainter purple for negative

    # Plot the NET PULSE Line on top (The Result)
    ax3.plot(df['Timestamp'], net_pulse, color=COLORS['pulse'], lw=2.5, label='Net Growth Pulse')

    # Plot the Threshold
    ax3.axhline(0.15, color=COLORS['threshold'], ls='--', lw=2, label='Goldilocks Threshold')

    ax3.set_title("Growth Drivers: Labor (Green) vs Mfg (Purple)", fontsize=14, fontweight='bold', color=COLORS['text'])
    ax3.legend(loc='upper left', fontsize=9, ncol=2)
    ax3.grid(True, color=COLORS['grid'])

    # --- CHART 4: RSI SPEEDOMETER ---
    last_rsi = df['RSI'].iloc[-1]
    ax4.plot(df['Timestamp'], df['RSI'], color=COLORS['rsi'], lw=2)
    ax4.axhline(70, color=COLORS['growth_neg'], ls=':', lw=2)
    ax4.axhline(30, color=COLORS['growth_pos'], ls=':', lw=2)
    ax4.set_title(f"SPY RSI: {last_rsi:.1f} (Tactical)", fontsize=14, fontweight='bold', color=COLORS['rsi'])
    ax4.set_ylim(0, 100)
    ax4.grid(True, color=COLORS['grid'])

    # Formatting
    for ax in [ax1, ax2, ax3, ax4]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H'))
        ax.tick_params(colors=COLORS['text'], rotation=30)
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['grid'])

    plt.savefig(OUTPUT_CHART, dpi=100, bbox_inches='tight')
    print(f"[SUCCESS] Dashboard updated. Chart 3 now uses 'Attribution Stacking' for readability.")

if __name__ == "__main__":
    create_dashboard()