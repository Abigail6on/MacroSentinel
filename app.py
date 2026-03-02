import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGIME_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
SMOOTHED_PATH = os.path.join(BASE_DIR, "data", "processed", "smoothed_indicators.csv")
RISK_PATH = os.path.join(BASE_DIR, "data", "processed", "risk_metrics.json")
PERFORMANCE_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
DASHBOARD_IMG_PATH = os.path.join(BASE_DIR, "output", "sentinel_pro_dashboard.png")

st.set_page_config(page_title="MacroSentinel | Global Macro AI", layout="wide")

st.title("MacroSentinel: AI-Driven Global Macro Fund")
st.markdown("An institutional quantitative framework fusing NLP Sentiment, Macroeconomic Data, and Machine Learning to dynamically navigate market regimes.")
st.divider()

@st.cache_data
def load_data():
    risk_data = {"VaR_95": "N/A", "CVaR_95": "N/A", "Max_Drawdown": "N/A"}
    if os.path.exists(RISK_PATH):
        with open(RISK_PATH, "r") as f:
            risk_data = json.load(f)
            
    latest_regime = "Unknown"
    ml_status = "Unknown"
    df = None
    
    if os.path.exists(REGIME_PATH):
        df = pd.read_csv(REGIME_PATH)
        
        # --- Institutional Time-Series Merge ---
        if os.path.exists(SMOOTHED_PATH):
            smooth_df = pd.read_csv(SMOOTHED_PATH)
            
            # 1. Force both columns into pure Python Datetime objects
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            smooth_df['Timestamp'] = pd.to_datetime(smooth_df['Timestamp'])
            
            # 2. Sort chronologically (strictly required for merge_asof)
            df = df.sort_values('Timestamp')
            smooth_df = smooth_df.sort_values('Timestamp')
            
            # 3. Merge As-Of: Grabs the most recent sentiment score for that exact stock price tick
            df = pd.merge_asof(df, smooth_df, on='Timestamp', direction='backward')

        if not df.empty:
            latest_regime = df.iloc[-1].get("Regime_V2", "Unknown")
            ml_status = df.iloc[-1].get("ML_Crash_Veto", False)
            
    perf_df = None
    if os.path.exists(PERFORMANCE_PATH):
        perf_df = pd.read_csv(PERFORMANCE_PATH)
        
    return risk_data, latest_regime, ml_status, df, perf_df

risk_data, current_regime, is_veto_active, history_df, perf_df = load_data()

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "🧠 Model Analytics & Logic", "🛡️ Risk & Decision Log"])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Market Regime", str(current_regime))
    col2.metric("ML Crash Veto", "ACTIVE 🚨" if is_veto_active else "Clear ✅")
    
    var_val = risk_data.get("VaR_95", 0)
    cvar_val = risk_data.get("CVaR_95", 0)
    
    if isinstance(var_val, (int, float)):
        col3.metric("95% Value at Risk (VaR)", f"{var_val * 100:.2f}%")
    else:
        col3.metric("95% Value at Risk (VaR)", var_val)
        
    if isinstance(cvar_val, (int, float)):
        col4.metric("Expected Shortfall (CVaR)", f"{cvar_val * 100:.2f}%")
    else:
        col4.metric("Expected Shortfall (CVaR)", cvar_val)

    st.divider()

    st.markdown("### Regime-Aware Performance Curve")
    if perf_df is not None and not perf_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=perf_df['Timestamp'], y=perf_df['Strategy_Value'], name='Sentinel Strategy', line=dict(color='#00ff00', width=2)))
        fig.add_trace(go.Scatter(x=perf_df['Timestamp'], y=perf_df['Benchmark_Value'], name='SPY Benchmark', line=dict(color='#888888', width=2)))
        fig.update_layout(yaxis_title="Cumulative Return", xaxis_title="Date", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Performance data is currently building.")

# ==========================================
# TAB 2: ADVANCED ANALYTICS (Version 2.0 Features)
# ==========================================
with tab2:

    st.markdown("### NLP Sentiment Alpha Generation")
    st.caption("Overlaying the AI's real-time News Sentiment (VADER) against the S&P 500. Proves that falling sentiment leads to market drawdowns.")
    
    if history_df is not None and 'SPY' in history_df.columns and 'Inflation_Sentiment' in history_df.columns:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig2.add_trace(
            go.Scatter(x=history_df['Timestamp'], y=history_df['SPY'], name="SPY Price", line=dict(color='blue')),
            secondary_y=False,
        )

        # Forward-fill normal gaps, Backward-fill the starting edge-case, then calculate rolling average
        history_df['Smoothed_Sentiment'] = history_df['Inflation_Sentiment'].ffill().bfill().rolling(7, min_periods=1).mean()
        
        fig2.add_trace(
            go.Scatter(x=history_df['Timestamp'], y=history_df['Smoothed_Sentiment'], name="Rolling NLP Sentiment", line=dict(color='orange', dash='dot')),
            secondary_y=True,
        )
        
        fig2.update_yaxes(title_text="<b>SPY Price</b>", secondary_y=False)
        fig2.update_yaxes(title_text="<b>News Sentiment (-1 to 1)</b>", secondary_y=True)
        fig2.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        
        st.plotly_chart(fig2, width='stretch')
    else:
        st.warning("NLP Sentiment data not found. Checking data pipeline integration...")
        
    st.divider()

    st.markdown("### Tactical Asset Correlation Matrix")
    st.caption("Validates the AI's diversification strategy. Assets with high correlation (red) move together. The AI hunts for low/negative correlation (blue) during defensive regimes.")
    
    if history_df is not None:
        price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
        avail_cols = [c for c in price_cols if c in history_df.columns]
        
        if len(avail_cols) > 1:
            corr_matrix = history_df[avail_cols].pct_change().corr()
            
            fig3 = px.imshow(corr_matrix, 
                             text_auto=".2f", 
                             aspect="auto",
                             color_continuous_scale='RdBu_r', 
                             zmin=-1, zmax=1)
            fig3.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig3, width='stretch')
        else:
            st.info("Gathering more asset pricing data to compute correlation.")

# ==========================================
# TAB 3: RISK & DECISION LOG
# ==========================================
with tab3:
    st.markdown("### Global Asset Allocation & Risk Maps")
    if os.path.exists(DASHBOARD_IMG_PATH):
        image = Image.open(DASHBOARD_IMG_PATH)
        st.image(image)
    else:
        st.warning("Dashboard image not found.")

    st.divider()

    st.markdown("### Under the Hood: AI Decision Log")
    st.caption("Live feed of the mathematical indicators driving the Regime Engine.")
    
    if history_df is not None:
        price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
        display_cols = [col for col in history_df.columns if col not in price_cols and col != 'Smoothed_Sentiment']
        
        priority_cols = ['Timestamp', 'Regime_V2', 'ML_Crash_Veto', 'VIX_Index', 'Real_Liquidity', 'Inflation_Sentiment']
        ordered_cols = [c for c in priority_cols if c in display_cols] + [c for c in display_cols if c not in priority_cols]
        
        st.dataframe(history_df[ordered_cols].tail(50).iloc[::-1], width='stretch')