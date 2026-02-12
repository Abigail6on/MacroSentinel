import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
ALLOCATION_DATA = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")
PRICE_DATA = os.path.join(BASE_DIR, "data", "processed", "live_prices.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

# BRIGHT COLOR PATTERN
REGIME_COLORS = {
    "Goldilocks (Growth)": "#2ecc71",
    "Goldilocks -> Tightening (Warning)": "#f1c40f",
    "Overheat (Inflationary)": "#e67e22",
    "Stagflation (High Risk)": "#e74c3c",
    "Deflationary Recession": "#3498db",
    "Neutral / Transitioning": "#95a5a6"
}

def create_dashboard():
    print("[INFO] Generating High-Resolution Upscaled Dashboard...")
    
    if not all(os.path.exists(f) for f in [REGIME_DATA, ALLOCATION_DATA, PRICE_DATA]):
        print("[ERROR] Required data missing.")
        return

    # Load and Sanitize
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    alloc_df = pd.read_csv(ALLOCATION_DATA)
    price_df = pd.read_csv(PRICE_DATA)
    for d in [alloc_df, price_df]:
        d['Ticker'] = d['Ticker'].astype(str).str.strip().str.upper()

    # Pre-process Sentiment
    df['Date'] = df['Timestamp'].dt.date
    daily_sentiment = df.groupby('Date')[['Monetary_Policy', 'Labor_Market']].mean()

    # SETUP STYLE - BRIGHT & CLEAR
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = '#f8f9fa'
    
    # UPSCALED FIGURE SIZE (24x18 inches)
    fig, axes = plt.subplots(2, 2, figsize=(24, 18)) 
    fig.suptitle('MACRO SENTINEL: SYSTEM STATUS', fontsize=40, fontweight='bold', color='#2c3e50', y=0.97)

    # --- 1. TOP LEFT: DAILY SENTIMENT ---
    daily_sentiment.plot(kind='bar', ax=axes[0,0], color=['#2980b9', '#27ae60'], alpha=0.8)
    axes[0,0].set_title('Daily Narrative Momentum', fontsize=22, fontweight='bold', pad=25)
    axes[0,0].set_xticklabels([d.strftime('%b %d') for d in daily_sentiment.index], rotation=0, fontsize=16)
    axes[0,0].legend(["Fed Mood", "Labor Health"], frameon=True, loc='upper left', fontsize=16)

    # --- 2. TOP RIGHT: MACRO TRENDS ---
    ax2_twin = axes[0, 1].twinx()
    axes[0, 1].plot(df['Timestamp'], df['Inflation_YoY'], color='#c0392b', lw=4, label='Inflation %')
    ax2_twin.plot(df['Timestamp'], df['Yield_Curve_10Y2Y'], color='#f39c12', lw=3, ls='--', label='Yield Curve')
    axes[0,1].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.setp(axes[0,1].get_xticklabels(), rotation=0, fontsize=16)
    axes[0,1].set_title('Hard Macro Timeline', fontsize=22, fontweight='bold', pad=25)
    axes[0,1].legend(loc='upper left', fontsize=16)

    # --- 3. BOTTOM LEFT: BALANCED EXPOSURE BARS ---
    counts = df['Regime_V2'].value_counts()
    colors = [REGIME_COLORS.get(x, '#bdc3c7') for x in counts.index]
    short_labels = [label.split('(')[0].strip() for label in counts.index]
    
    axes[1, 0].barh(short_labels, counts.values, color=colors, edgecolor='black', alpha=0.8)
    axes[1, 0].set_title('Regime Exposure (Cumulative Hours)', fontsize=22, fontweight='bold', pad=25)
    axes[1, 0].invert_yaxis()
    axes[1, 0].tick_params(axis='y', labelsize=18)
    axes[1, 0].tick_params(axis='x', labelsize=16)

    # --- 4. BOTTOM RIGHT: TACTICAL ALLOCATION TABLE ---
    axes[1, 1].axis('off')
    pulse_df = pd.merge(alloc_df, price_df, on='Ticker', how='left').fillna("N/A")
    table_data = []
    for _, row in pulse_df.iterrows():
        change = row['Change_Pct']
        icon = "▲" if (isinstance(change, float) and change > 0) else "▼"
        change_str = f"{icon} {change:.2f}%" if isinstance(change, float) else "N/A"
        table_data.append([row['Ticker'], f"{row['Weight']*100:.0f}%", f"${row['Price']:.2f}", change_str])

    table = axes[1, 1].table(cellText=table_data, colLabels=['Ticker', 'Weight', 'Price', '24h Change'], 
                             loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(18) # Scaled up font
    table.scale(1.0, 5.0)  # Increased vertical padding for a "larger" feel
    
    # Style Header
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#34495e')

    latest_regime = df['Regime_V2'].iloc[-1]
    axes[1, 1].text(0.5, 0.95, f"CURRENT REGIME: {latest_regime.upper()}", 
                    fontsize=20, ha='center', fontweight='bold', color=REGIME_COLORS.get(latest_regime, '#2c3e50'))

    # ADJUST LAYOUT FOR LARGE CANVAS
    plt.tight_layout(rect=[0.03, 0.03, 0.97, 0.93]) 
    plt.subplots_adjust(wspace=0.25, hspace=0.3) 
    
    # HIGH RESOLUTION SAVE (DPI=250)
    plt.savefig(OUTPUT_CHART, dpi=250)
    print(f"[SUCCESS] High-Res Dashboard saved to {OUTPUT_CHART}")

if __name__ == "__main__":
    create_dashboard()