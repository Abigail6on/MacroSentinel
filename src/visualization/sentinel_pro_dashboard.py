import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
NEWS_PATH = os.path.join(BASE_DIR, "data", "raw", "news_stream_history.csv")
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

    # Set up the figure grid with a clean 2x2 layout
    plt.style.use('default')
    fig = plt.figure(figsize=(20, 12), facecolor='white', layout='constrained')
    
    # A 2x2 grid. The left column gets slightly more width (1.6) than the right (1.4)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1.4])
    
    # --- SUBPLOT 1: Equity Curve (Top Left) ---
    ax1 = fig.add_subplot(gs[0, 0])
    
    # 1. Plot SPY Benchmark (Grey, dashed) to match Streamlit
    ax1.plot(bt_df['Timestamp'], bt_df['Benchmark_Value'], color='#888888', linewidth=1.5, linestyle='--', label='SPY Benchmark')
    
    # 2. Add SHY (Cash) Baseline safely using .fillna(0)
    if 'SHY_Ret' in bt_df.columns:
        shy_cum = (1 + bt_df['SHY_Ret'].fillna(0)).cumprod()
        ax1.plot(bt_df['Timestamp'], shy_cum, label='SHY (Cash Base)', color='#17a2b8', linewidth=1.5, linestyle=':')
        
    # 3. Plot MacroSentinel Strategy (Green, solid, thick) last so it sits on top!
    ax1.plot(bt_df['Timestamp'], bt_df['Strategy_Value'], color='#00ff00', linewidth=2.5, label='MacroSentinel Strategy')

    ax1.set_title("Strategy vs Benchmark Equity Curve", fontsize=14, fontweight='bold', color='black')
    ax1.legend(loc='upper left')
    ax1.grid(color='#e0e0e0', linestyle=':', alpha=0.8)
    ax1.set_ylabel("Cumulative Return")
    
    regimes = bt_df['Regime_V2'].unique()
    colors = {'Goldilocks (Growth)': '#d4edda', 'Neutral / Transitioning': '#fff3cd', 'Defensive (Contraction)': '#f8d7da'}
    
    for i in range(1, len(bt_df)):
        regime = bt_df['Regime_V2'].iloc[i]
        c = colors.get(regime, '#f4f4f4')
        ax1.axvspan(bt_df['Timestamp'].iloc[i-1], bt_df['Timestamp'].iloc[i], color=c, alpha=0.4, lw=0)
        
    # --- SUBPLOT 2: Target Allocation (Top Right) ---
    ax2 = fig.add_subplot(gs[0, 1])
    if not alloc_df.empty:
        alloc_df = alloc_df[alloc_df['Weight'] > 0].sort_values(by='Weight', ascending=True)
        ax2.barh(alloc_df['Ticker'], alloc_df['Weight'] * 100, color='#3399ff', height=0.6, edgecolor='black', linewidth=0.5)
        ax2.set_title(f"Target Allocation\n(Regime: {alloc_df['Regime'].iloc[0]})", fontsize=14, fontweight='bold', color='black')
        ax2.set_xlabel("Weight (%)", fontweight='bold')
        
        ax2.set_ylim(-0.5, len(alloc_df) - 0.5)
        max_weight = alloc_df['Weight'].max() * 100
        ax2.set_xlim(0, max_weight + 20) 
        
        for i, v in enumerate(alloc_df['Weight']):
            ax2.text(v * 100 + 2, i, f"{v*100:.0f}%", color='black', va='center', fontweight='bold')
            
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
    
    # --- SUBPLOT 3: Macro & Liquidity (Bottom Left) ---
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(bt_df['Timestamp'], bt_df['Real_Liquidity'], color='#ff6600', linewidth=2)
    ax3.set_title("Federal Reserve Real Liquidity\n(M2 Growth - CPI)", fontsize=14, fontweight='bold', color='black')
    ax3.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax3.fill_between(bt_df['Timestamp'], bt_df['Real_Liquidity'], 0, where=(bt_df['Real_Liquidity'] >= 0), color='#28a745', alpha=0.2)
    ax3.fill_between(bt_df['Timestamp'], bt_df['Real_Liquidity'], 0, where=(bt_df['Real_Liquidity'] < 0), color='#dc3545', alpha=0.2)
    ax3.tick_params(axis='x', rotation=45)

    # --- SUBPLOT 4: Sentiment Heatmap (Bottom Right) ---
    ax4 = fig.add_subplot(gs[1, 1])
    
    recent_news = news_df.tail(100).copy()
    
    # Drop duplicate headlines so matplotlib plots 5 distinct bars
    recent_news = recent_news.drop_duplicates(subset=['Headline'])
    
    recent_news['Abs_Score'] = recent_news['Sentiment'].abs()
    top_news = recent_news.sort_values(by='Abs_Score', ascending=False).head(5).sort_values(by='Sentiment')
    
    if not top_news.empty:
        # Reduced width to 55 to fit the slightly narrower 2x2 right column cleanly
        labels = [textwrap.fill(h, width=55) for h in top_news['Headline']]
        scores = top_news['Sentiment']
        
        bar_colors = ['#dc3545' if s < 0 else '#28a745' for s in scores]
        
        bars = ax4.barh(labels, scores, color=bar_colors, edgecolor='black', linewidth=0.5)
        ax4.set_title("NLP Sentiment Intensity Map\n(Top 5 Active Catalysts)", fontsize=14, fontweight='bold', color='black')
        ax4.axvline(0, color='black', linewidth=1)
        ax4.set_xlabel("VADER Intensity Score")
        ax4.set_xlim(-1.2, 1.2)
        
        for bar, score in zip(bars, scores):
            x_offset = 0.05 if score > 0 else -0.15
            ax4.text(score + x_offset, bar.get_y() + bar.get_height()/2, f"{score:.2f}", 
                     color='black', va='center', fontweight='bold')
    else:
        ax4.text(0.5, 0.5, "No News Data Available", ha='center', va='center', color='black')
        
    # Formatting X-Axis
    for ax in [ax1, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        
    # Save Output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[SUCCESS] Dashboard saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_dashboard()