import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
ALLOCATION_DATA = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")
PRICE_DATA = os.path.join(BASE_DIR, "data", "processed", "live_prices.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

def create_dashboard():
    if not all(os.path.exists(f) for f in [REGIME_DATA, ALLOCATION_DATA, PRICE_DATA]):
        print("[ERROR] Required data missing. Ensure engine, allocator, and price_tracker have run.")
        return

    # Load Data
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    alloc_df = pd.read_csv(ALLOCATION_DATA)
    price_df = pd.read_csv(PRICE_DATA)
    sns.set_theme(style="whitegrid")

    # Merge Allocation and Prices for the "Market Pulse"
    pulse_df = pd.merge(alloc_df, price_df, on='Ticker', how='left')

    fig, axes = plt.subplots(2, 2, figsize=(18, 13))
    fig.suptitle('Macro Sentinel: Multi-Factor Analysis & Live Market Pulse', fontsize=24, fontweight='bold', y=0.98)

    # 1. Sentiment Streams (Top Left)
    axes[0, 0].plot(df['Timestamp'], df['Monetary_Policy'], label='Fed Sentiment', color='#2c3e50', lw=2.5)
    axes[0, 0].plot(df['Timestamp'], df['Labor_Market'], label='Labor Market', color='#27ae60', lw=2.5)
    axes[0, 0].set_title('Proprietary Sentiment Streams', fontsize=15, fontweight='semibold')
    axes[0, 0].legend(loc='upper left')

    # 2. Risk Matrix (Top Right)
    scatter = axes[0, 1].scatter(df['Inflation_YoY'], df['Yield_Curve_10Y2Y'], 
                                 c=range(len(df)), cmap='Blues', s=120, edgecolors='black', alpha=0.6)
    cbar = fig.colorbar(scatter, ax=axes[0, 1])
    cbar.set_label('Time Progression (Hourly)', rotation=270, labelpad=15)
    axes[0, 1].scatter(df['Inflation_YoY'].iloc[-1], df['Yield_Curve_10Y2Y'].iloc[-1], 
                       color='#e74c3c', marker='*', s=350, edgecolors='black', label='Current State', zorder=5)
    axes[0, 1].axhline(0, color='black', lw=1, alpha=0.5)
    axes[0, 1].axvline(3.0, color='#c0392b', linestyle='--', alpha=0.5)
    axes[0, 1].set_title('Systemic Risk: Inflation vs. Yield Spread', fontsize=15, fontweight='semibold')
    axes[0, 1].set_xlabel('Inflation (YoY %)')
    axes[0, 1].set_ylabel('Yield Spread (10Y-2Y)')
    axes[0, 1].legend()

    # 3. Regime Distribution (Bottom Left)
    regime_counts = df['Regime_V2'].value_counts()
    axes[1, 0].pie(regime_counts, labels=regime_counts.index, autopct='%1.1f%%', 
                   colors=sns.color_palette('viridis', n_colors=len(regime_counts)), startangle=140)
    axes[1, 0].set_title('Historical Regime Distribution', fontsize=15, fontweight='semibold')

    # 4. Market Pulse & Tactical Allocation (Bottom Right)
    axes[1, 1].axis('off')
    strategy = alloc_df['Strategy'].iloc[0]
    regime = alloc_df['Regime'].iloc[0]

    # Prepare table data: Asset | Weight | Live Price | 24h Change
    table_data = []
    for _, row in pulse_df.iterrows():
        change_color = "▲" if row['Change_Pct'] > 0 else "▼"
        table_data.append([
            row['Ticker'], 
            f"{row['Weight']*100:.0f}%", 
            f"${row['Price']:.2f}", 
            f"{change_color} {row['Change_Pct']:.2f}%"
        ])

    the_table = axes[1, 1].table(cellText=table_data, colLabels=['Asset', 'Target Weight', 'Live Price', '24h Change'], 
                                  loc='center', cellLoc='center')
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(12)
    the_table.scale(1.1, 2.5)
    
    # Strategy Highlights
    axes[1, 1].text(0.5, 0.90, f"DETECTED REGIME: {regime}", fontsize=12, ha='center', fontweight='bold', color='#34495e')
    axes[1, 1].text(0.5, 0.82, f"ACTIVE STRATEGY: {strategy}", fontsize=16, ha='center', fontweight='bold', color='#2980b9')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    os.makedirs(os.path.dirname(OUTPUT_CHART), exist_ok=True)
    plt.savefig(OUTPUT_CHART, dpi=150)
    print(f"[SUCCESS] Live Dashboard generated: {OUTPUT_CHART}")

if __name__ == "__main__":
    create_dashboard()