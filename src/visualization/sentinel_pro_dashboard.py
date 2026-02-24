import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import textwrap

# Setup Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
NEWS_PATH = os.path.join(BASE_DIR, "data", "raw", "news_stream_history.csv")
# Corrected Filename
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "sentinel_pro_dashboard.png")

def build_dashboard():
    print("--- Generating Sentinel Pro Dashboard ---")
    
    # 1. Load Data
    try:
        bt_df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"))
        bt_df['Timestamp'] = pd.to_datetime(bt_df['Timestamp'])
        
        alloc_df = pd.read_csv(os.path.join(DATA_DIR, "target_allocation.csv"))
        
        news_df = pd.read_csv(NEWS_PATH)
        news_df['Timestamp'] = pd.to_datetime(news_df['Timestamp'])
    except Exception as e:
        print(f"[ERROR] Could not load data for dashboard: {e}")
        return

    # Set up the figure grid (Light Theme)
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 12), facecolor='white')
    gs = fig.add_gridspec(2, 3)
    
    # --- SUBPLOT 1: Equity Curve (Top Left, Spans 2 columns) ---
    ax1 = fig.add_subplot(gs[0, :2])
    # Darker blue and purple lines for visibility on white
    ax1.plot(bt_df['Timestamp'], bt_df['Strategy_Value'], color='#0055aa', linewidth=2.5, label='MacroSentinel Strategy')
    ax1.plot(bt_df['Timestamp'], bt_df['Benchmark_Value'], color='#aa00aa', linewidth=1.5, linestyle='--', label='SPY Benchmark')
    ax1.set_title("Strategy vs Benchmark Equity Curve", fontsize=14, fontweight='bold', color='black')
    ax1.legend(loc='upper left')
    ax1.grid(color='#e0e0e0', linestyle=':', alpha=0.8)
    ax1.set_ylabel("Cumulative Return")
    
    # Add Regime Shading to Equity Curve (Soft Pastels)
    regimes = bt_df['Regime_V2'].unique()
    colors = {'Goldilocks (Growth)': '#d4edda', 'Neutral / Transitioning': '#fff3cd', 'Defensive (Contraction)': '#f8d7da'}
    
    for i in range(1, len(bt_df)):
        regime = bt_df['Regime_V2'].iloc[i]
        c = colors.get(regime, '#f4f4f4')
        ax1.axvspan(bt_df['Timestamp'].iloc[i-1], bt_df['Timestamp'].iloc[i], color=c, alpha=0.4, lw=0)
        
    # --- SUBPLOT 2: Target Allocation (Top Right) ---
    ax2 = fig.add_subplot(gs[0, 2])
    if not alloc_df.empty:
        alloc_df = alloc_df[alloc_df['Weight'] > 0].sort_values(by='Weight', ascending=True)
        ax2.barh(alloc_df['Ticker'], alloc_df['Weight'] * 100, color='#3399ff')
        ax2.set_title(f"Target Allocation\n(Regime: {alloc_df['Regime'].iloc[0]})", fontsize=14, fontweight='bold', color='black')
        ax2.set_xlabel("Weight (%)")
        for i, v in enumerate(alloc_df['Weight']):
            ax2.text(v * 100 + 1, i, f"{v*100:.0f}%", color='black', va='center', fontweight='bold')
    
    # --- SUBPLOT 3: Macro & Liquidity (Bottom Left) ---
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(bt_df['Timestamp'], bt_df['Real_Liquidity'], color='#ff6600', linewidth=2)
    ax3.set_title("Federal Reserve Real Liquidity (M2 Growth - CPI)", fontsize=14, fontweight='bold', color='black')
    ax3.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax3.fill_between(bt_df['Timestamp'], bt_df['Real_Liquidity'], 0, where=(bt_df['Real_Liquidity'] >= 0), color='#28a745', alpha=0.2)
    ax3.fill_between(bt_df['Timestamp'], bt_df['Real_Liquidity'], 0, where=(bt_df['Real_Liquidity'] < 0), color='#dc3545', alpha=0.2)
    ax3.tick_params(axis='x', rotation=45)

    # --- SUBPLOT 4: NEW! Sentiment Heatmap (Bottom Middle & Right, Spans 2 columns) ---
    ax4 = fig.add_subplot(gs[1, 1:])
    
    recent_news = news_df.tail(100).copy()
    recent_news['Abs_Score'] = recent_news['Sentiment'].abs()
    top_news = recent_news.sort_values(by='Abs_Score', ascending=False).head(5).sort_values(by='Sentiment')
    
    if not top_news.empty:
        labels = [textwrap.fill(h, width=65) for h in top_news['Headline']]
        scores = top_news['Sentiment']
        
        # Color Code: Institutional Red/Green
        bar_colors = ['#dc3545' if s < 0 else '#28a745' for s in scores]
        
        bars = ax4.barh(labels, scores, color=bar_colors, edgecolor='black', linewidth=0.5)
        ax4.set_title("NLP Sentiment Intensity Map (Top 5 Active Catalysts)", fontsize=14, fontweight='bold', color='black')
        ax4.axvline(0, color='black', linewidth=1)
        ax4.set_xlabel("VADER Intensity Score")
        ax4.set_xlim(-1.2, 1.2)
        
        for bar, score in zip(bars, scores):
            x_offset = 0.05 if score > 0 else -0.15
            ax4.text(score + x_offset, bar.get_y() + bar.get_height()/2, f"{score:.2f}", 
                     color='black', va='center', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, "No News Data Available", ha='center', va='center', color='black')
        
    # Formatting X-Axis across the board
    for ax in [ax1, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
    plt.tight_layout()
    
    # Save Output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[SUCCESS] Dashboard saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_dashboard()