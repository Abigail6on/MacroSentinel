import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Environment-Agnostic Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
OUTPUT_CHART = os.path.join(BASE_DIR, "output", "macro_sentinel_dashboard.png")

def create_dashboard():
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] No regime data found at {REGIME_DATA}. Run regime_engine_v2.py first.")
        return

    # Load and setup
    df = pd.read_csv(REGIME_DATA, parse_dates=['Timestamp'])
    sns.set_theme(style="whitegrid")

    # Create a 2x2 Dashboard
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Macro Sentinel: Multi-Factor Regime Analysis', fontsize=22, fontweight='bold', y=0.98)

    # 1. Sentiment Streams (Top Left)
    axes[0, 0].plot(df['Timestamp'], df['Monetary_Policy'], label='Fed Sentiment', color='#2c3e50', lw=2)
    axes[0, 0].plot(df['Timestamp'], df['Labor_Market'], label='Labor Market', color='#27ae60', lw=2)
    axes[0, 0].plot(df['Timestamp'], df['Manufacturing'], label='Industrial Pulse', color='#e67e22', lw=2, alpha=0.7)
    axes[0, 0].set_title('Real-Time Sentiment Indicators', fontsize=14, fontweight='semibold')
    axes[0, 0].legend(loc='upper left')
    axes[0, 0].set_ylabel('Smoothed Sentiment Score')

    # 2. Risk Matrix (Top Right)
    scatter = axes[0, 1].scatter(df['Inflation_YoY'], df['Yield_Curve_10Y2Y'], 
                                 c=range(len(df)), cmap='Blues', s=100, edgecolors='black', alpha=0.6)
    axes[0, 1].axhline(0, color='red', linestyle='--', alpha=0.5)
    axes[0, 1].axvline(3.0, color='red', linestyle='--', alpha=0.5)
    axes[0, 1].set_title('Systemic Risk: Inflation vs. Yield Spread', fontsize=14, fontweight='semibold')
    axes[0, 1].set_xlabel('Inflation (YoY %)')
    axes[0, 1].set_ylabel('Yield Spread (10Y-2Y)')

    # 3. Regime Distribution (Bottom Left)
    regime_counts = df['Regime_V2'].value_counts()
    axes[1, 0].pie(regime_counts, labels=regime_counts.index, autopct='%1.1f%%', 
                   colors=sns.color_palette('viridis', n_colors=len(regime_counts)),
                   startangle=140)
    axes[1, 0].set_title('Time-in-Regime Distribution', fontsize=14, fontweight='semibold')

    # 4. Growth Momentum Pulse (Bottom Right)
    growth_pulse = (df['Labor_Market'] * 0.6) + (df['Manufacturing'] * 0.4)
    axes[1, 1].fill_between(df['Timestamp'], growth_pulse, color="#2ecc71", alpha=0.3, label='Growth Pulse')
    axes[1, 1].plot(df['Timestamp'], growth_pulse, color="#27ae60", lw=2)
    axes[1, 1].set_title('Real-Time Growth Momentum', fontsize=14, fontweight='semibold')
    axes[1, 1].set_ylim(-1, 1)
    axes[1, 1].axhline(0, color='black', lw=1)
    axes[1, 1].legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    os.makedirs(os.path.dirname(OUTPUT_CHART), exist_ok=True)
    plt.savefig(OUTPUT_CHART)
    print(f"[SUCCESS] Dashboard generated: {OUTPUT_CHART}")

if __name__ == "__main__":
    create_dashboard()