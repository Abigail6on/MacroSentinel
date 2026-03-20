import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import json
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
NEWS_PATH = os.path.join(BASE_DIR, "data", "raw", "news_stream_history.csv")
SHAP_PATH = os.path.join(DATA_DIR, "shap_explanation.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "sentinel_pro_dashboard.png")

def build_dashboard():
    print("--- Generating Sentinel Pro Master Dashboard ---")
    
    # 1. Load Data
    try:
        bt_df = pd.read_csv(os.path.join(DATA_DIR, "backtest_results.csv"))
        bt_df['Timestamp'] = pd.to_datetime(bt_df['Timestamp'])
        bt_df = bt_df.ffill().bfill()
        
        alloc_df = pd.read_csv(os.path.join(DATA_DIR, "target_allocation.csv"))
        
        news_df = pd.read_csv(NEWS_PATH)
        news_df['Timestamp'] = pd.to_datetime(news_df['Timestamp'])
        
        regime_df = pd.read_csv(os.path.join(DATA_DIR, "regime_v2_status.csv"))
        regime_df['Timestamp'] = pd.to_datetime(regime_df['Timestamp'])
        regime_df = regime_df.ffill().bfill()
        
        with open(SHAP_PATH, "r") as f:
            shap_data = json.load(f)
            
    except Exception as e:
        print(f"[ERROR] Could not load data for dashboard: {e}")
        return

    # 2. Set up the figure grid
    plt.style.use('default')
    fig = plt.figure(figsize=(24, 16), facecolor='white')
    
    # NEW UI FEATURE: Master Title Alert System
    current_regime = regime_df['Regime_V2'].iloc[-1]
    
    # Safely extract boolean veto status (handles strings or bools)
    raw_veto = regime_df['ML_Crash_Veto'].iloc[-1]
    ml_veto = str(raw_veto).lower() == 'true' or raw_veto == True
    
    status_color = '#dc3545' if ml_veto else '#28a745'
    veto_text = "ACTIVE (Crash Detected)" if ml_veto else "Standby (Safe)"
    
    fig.suptitle(f"Sentinel Pro Master Dashboard | Regime: {current_regime} | ML Veto: {veto_text}", 
                 fontsize=24, fontweight='bold', color=status_color, y=0.96)
                 
    gs = fig.add_gridspec(3, 2, width_ratios=[1.2, 1.2], height_ratios=[1.2, 1, 1.2])
    
    # --- ROW 1: Equity Curve (Top Left) ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(bt_df['Timestamp'], bt_df['Benchmark_Value'], color='#888888', linewidth=1.5, linestyle='--', label='SPY Benchmark')
    if 'SHY_Ret' in bt_df.columns:
        shy_cum = (1 + bt_df['SHY_Ret'].fillna(0)).cumprod()
        ax1.plot(bt_df['Timestamp'], shy_cum, label='SHY (Cash Base)', color='#17a2b8', linewidth=1.5, linestyle=':')
    ax1.plot(bt_df['Timestamp'], bt_df['Strategy_Value'], color='#00ff00', linewidth=2.5, alpha=0.8, label='MacroSentinel (Net of Fees)')
    ax1.set_title("Strategy vs Benchmark Equity Curve", fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(color='#e0e0e0', linestyle=':', alpha=0.8)
    ax1.set_ylabel("Cumulative Return")
    
    colors = {'Goldilocks': '#d4edda', 'Neutral': '#fff3cd', 'Stagflation': '#f8d7da', 'Defensive': '#dc3545'}
    for i in range(1, len(bt_df)):
        regime = str(bt_df['Regime_V2'].iloc[i]).split(' ')[0]
        c = colors.get(regime, '#f4f4f4')
        ax1.axvspan(bt_df['Timestamp'].iloc[i-1], bt_df['Timestamp'].iloc[i], color=c, alpha=0.4, lw=0)
        
    # --- ROW 1: Target Allocation (Top Right) ---
    ax2 = fig.add_subplot(gs[0, 1])
    if not alloc_df.empty:
        alloc_df = alloc_df[alloc_df['Weight'] > 0].sort_values(by='Weight', ascending=True)
        ax2.barh(alloc_df['Ticker'], alloc_df['Weight'] * 100, color='#3399ff', height=0.6, edgecolor='black', linewidth=0.5)
        ax2.set_title(f"Target Allocation\n(Regime: {alloc_df['Regime'].iloc[0]})", fontsize=14, fontweight='bold')
        ax2.set_xlabel("Weight (%)", fontweight='bold')
        ax2.set_xlim(0, (alloc_df['Weight'].max() * 100) + 20)
        for i, v in enumerate(alloc_df['Weight']):
            ax2.text(v * 100 + 2, i, f"{v*100:.0f}%", color='black', va='center', fontweight='bold')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
    
    # --- ROW 2: Market Risk / VIX (Middle Left) ---
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(regime_df['Timestamp'], regime_df['VIX_Index'], color='#ff4c4c', linewidth=2, label='VIX Level')
    ax3.set_title("Market Risk (VIX Fear Gauge)", fontsize=14, fontweight='bold')
    ax3.axhline(20, color='black', linestyle='--', alpha=0.5, label='High Risk Threshold (>20)')
    ax3.fill_between(regime_df['Timestamp'], regime_df['VIX_Index'], 20, where=(regime_df['VIX_Index'] >= 20), color='#dc3545', alpha=0.3)
    ax3.fill_between(regime_df['Timestamp'], regime_df['VIX_Index'], 20, where=(regime_df['VIX_Index'] < 20), color='#28a745', alpha=0.2)
    ax3.set_ylabel("Volatility Index (VIX)")
    ax3.legend(loc='upper right')
    ax3.grid(color='#e0e0e0', linestyle=':', alpha=0.8)

    # --- ROW 2: SHAP Explainable AI (Middle Right) ---
    ax5 = fig.add_subplot(gs[1, 1])
    shap_series = pd.Series(shap_data)
    top_shap = shap_series.reindex(shap_series.abs().sort_values(ascending=False).index).head(7).sort_values(ascending=True)
    
    shap_colors = ['#dc3545' if val > 0 else '#28a745' for val in top_shap.values]
    bars = ax5.barh(top_shap.index, top_shap.values, color=shap_colors, edgecolor='black', linewidth=0.5)
    ax5.set_title("XGBoost Brain: Real-Time SHAP Explainer\n(Red = Pushing to Crash | Green = Keeping Safe)", fontsize=14, fontweight='bold')
    ax5.axvline(0, color='black', linewidth=1)
    ax5.set_xlabel("Impact on ML Prediction")
    
    max_shap = top_shap.abs().max()
    pad = max_shap * 0.02 if max_shap > 0 else 0.01
    ax5.set_xlim(top_shap.min() - (max_shap * 0.3), top_shap.max() + (max_shap * 0.3))
    
    for bar, score in zip(bars, top_shap.values):
        if score >= 0:
            ax5.text(score + pad, bar.get_y() + bar.get_height()/2, f"{score:.4f}", color='black', va='center', ha='left', fontweight='bold')
        else:
            ax5.text(score - pad, bar.get_y() + bar.get_height()/2, f"{score:.4f}", color='black', va='center', ha='right', fontweight='bold')

    # --- ROW 3: Sentiment Heatmap (Bottom Spread) ---
    ax4 = fig.add_subplot(gs[2, :])
    recent_news = news_df.tail(100).drop_duplicates(subset=['Headline']).copy()
    recent_news['Abs_Score'] = recent_news['Sentiment'].abs()
    top_news = recent_news.sort_values(by='Abs_Score', ascending=False).head(5).sort_values(by='Sentiment')
    
    if not top_news.empty:
        labels = [textwrap.fill(h, width=80) for h in top_news['Headline']]
        scores = top_news['Sentiment']
        bar_colors = ['#dc3545' if s < 0 else '#28a745' for s in scores]
        bars = ax4.barh(labels, scores, color=bar_colors, edgecolor='black', linewidth=0.5)
        ax4.set_title("NLP Sentiment Intensity Map (Top Catalysts)", fontsize=14, fontweight='bold')
        ax4.axvline(0, color='black', linewidth=1)
        ax4.set_xlabel("VADER Intensity Score")
        ax4.set_xlim(-1.2, 1.2)
        
        for bar, score in zip(bars, scores):
            offset = 0.03 if score > 0 else -0.08
            ax4.text(score + offset, bar.get_y() + bar.get_height()/2, f"{score:.2f}", color='black', va='center', fontweight='bold')
        
    # Formatting X-Axis Timeframes
    for ax in [ax1, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.tick_params(axis='x', rotation=45)
        
    plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"[SUCCESS] Dashboard saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_dashboard()