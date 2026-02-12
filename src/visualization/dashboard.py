import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
ALLOCATION_DATA = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

def create_dashboard():
    if not os.path.exists(REGIME_DATA) or not os.path.exists(ALLOCATION_DATA):
        print("[ERROR] Data missing. Run engine and allocator first.")
        return

    # Load Data
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    alloc_df = pd.read_csv(ALLOCATION_DATA)
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Macro Sentinel: Multi-Factor Analysis & Tactical Allocation', fontsize=22, fontweight='bold', y=0.98)

    # 1. Sentiment Streams (Top Left)
    axes[0, 0].plot(df['Timestamp'], df['Monetary_Policy'], label='Fed Sentiment', color='#2c3e50', lw=2)
    axes[0, 0].plot(df['Timestamp'], df['Labor_Market'], label='Labor Market', color='#27ae60', lw=2)
    axes[0, 0].set_title('Real-Time Sentiment Indicators', fontsize=14, fontweight='semibold')
    axes[0, 0].legend(loc='upper left')

    # 2. Risk Matrix (Top Right)
    scatter = axes[0, 1].scatter(df['Inflation_YoY'], df['Yield_Curve_10Y2Y'], 
                                 c=range(len(df)), cmap='Blues', s=100, edgecolors='black', alpha=0.6)
    cbar = fig.colorbar(scatter, ax=axes[0, 1])
    cbar.set_label('Time Progression', rotation=270, labelpad=15)
    axes[0, 1].scatter(df['Inflation_YoY'].iloc[-1], df['Yield_Curve_10Y2Y'].iloc[-1], 
                       color='red', marker='*', s=250, label='Current')
    axes[0, 1].set_title('Systemic Risk: Inflation vs. Yield', fontsize=14, fontweight='semibold')
    axes[0, 1].legend()

    # 3. Regime Distribution (Bottom Left)
    regime_counts = df['Regime_V2'].value_counts()
    axes[1, 0].pie(regime_counts, labels=regime_counts.index, autopct='%1.1f%%', 
                   colors=sns.color_palette('viridis', n_colors=len(regime_counts)), startangle=140)
    axes[1, 0].set_title('Time-in-Regime Distribution', fontsize=14, fontweight='semibold')

    # 4. TACTICAL ALLOCATION TABLE (Bottom Right)
    axes[1, 1].axis('off')
    strategy_name = alloc_df['Strategy'].iloc[0]
    regime_name = alloc_df['Regime'].iloc[0]
    
    # Table Styling
    table_data = alloc_df[['Ticker', 'Weight']].copy()
    table_data['Weight'] = (table_data['Weight'] * 100).astype(int).astype(str) + '%'
    
    the_table = axes[1, 1].table(cellText=table_data.values, colLabels=['Asset', 'Weight'], 
                                  loc='center', cellLoc='center')
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(12)
    the_table.scale(1, 2)
    
    axes[1, 1].text(0.5, 0.85, f"Strategy: {strategy_name}", fontsize=14, 
                    fontweight='bold', ha='center', color='#2980b9')
    axes[1, 1].text(0.5, 0.78, f"Detected Regime: {regime_name}", fontsize=11, 
                    ha='center', style='italic')
    axes[1, 1].set_title('Target Portfolio Allocation', fontsize=14, fontweight='semibold', pad=20)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    os.makedirs(os.path.dirname(OUTPUT_CHART), exist_ok=True)
    plt.savefig(OUTPUT_CHART)
    print(f"[SUCCESS] Dashboard refreshed at {OUTPUT_CHART}")

if __name__ == "__main__":
    create_dashboard()