import streamlit as st
import pandas as pd
import numpy as np
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

# --- INTERACTIVE SIDEBAR ---
with st.sidebar:
    st.header("Risk Parameters")
    st.markdown("Interact with the model's risk tolerance.")
    
    conf_level = st.slider("VaR Confidence Level (%)", min_value=90, max_value=99, value=95, step=1)
    st.caption("Adjust the slider to recalculate the Value at Risk (VaR) and Expected Shortfall dynamically on the historical equity curve.")

st.title("MacroSentinel: AI-Driven Global Macro Fund")
st.markdown("An institutional quantitative framework fusing NLP Sentiment, Macroeconomic Data, and Machine Learning to dynamically navigate market regimes.")
st.divider()

# --- DATA LOADING ---
@st.cache_data
def load_data():
    risk_data = {"VaR_95": "N/A", "CVaR_95": "N/A", "Max_Drawdown": "N/A"}
    if os.path.exists(RISK_PATH):
        with open(RISK_PATH, "r") as f:
            risk_data = json.load(f)
            
    latest_regime = "Unknown"
    ml_status = False
    df = None
    
    if os.path.exists(REGIME_PATH):
        df = pd.read_csv(REGIME_PATH)
        
        if os.path.exists(SMOOTHED_PATH):
            smooth_df = pd.read_csv(SMOOTHED_PATH)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            smooth_df['Timestamp'] = pd.to_datetime(smooth_df['Timestamp'])
            df = df.sort_values('Timestamp')
            smooth_df = smooth_df.sort_values('Timestamp')
            df = pd.merge_asof(df, smooth_df, on='Timestamp', direction='backward')
            df = df.ffill().bfill()
            
        if not df.empty:
            latest_regime = df.iloc[-1].get("Regime_V2", "Unknown")
            ml_status = df.iloc[-1].get("ML_Crash_Veto", False)
            
    perf_df = None
    if os.path.exists(PERFORMANCE_PATH):
        perf_df = pd.read_csv(PERFORMANCE_PATH)
        
    return risk_data, latest_regime, ml_status, df, perf_df

risk_data, current_regime, is_veto_active, history_df, perf_df = load_data()

# --- DYNAMIC MATH CALCULATION ---
dynamic_var = 0
dynamic_cvar = 0

if perf_df is not None and not perf_df.empty and 'Strategy_Value' in perf_df.columns:
    returns = perf_df['Strategy_Value'].pct_change().dropna()
    if len(returns) > 0:
        var_percentile = 100 - conf_level
        dynamic_var = np.percentile(returns, var_percentile)
        
        tail_returns = returns[returns <= dynamic_var]
        if len(tail_returns) > 0:
            dynamic_cvar = tail_returns.mean()
        else:
            dynamic_cvar = dynamic_var

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["Executive Summary", "Model Analytics & Logic", "Risk & Decision Log"])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Market Regime", str(current_regime))
    col2.metric("ML Crash Veto", "ACTIVE" if is_veto_active else "CLEAR")
    
    col3.metric(f"{conf_level}% Value at Risk (VaR)", f"{dynamic_var * 100:.2f}%")
    col4.metric(f"{conf_level}% Expected Shortfall (CVaR)", f"{dynamic_cvar * 100:.2f}%")

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
# TAB 2: ADVANCED ANALYTICS 
# ==========================================
with tab2:
    st.markdown("### NLP Sentiment Alpha Generation")
    st.caption("Overlaying the AI's real-time News Sentiment (VADER) against the S&P 500.")
    
    if history_df is not None and 'SPY' in history_df.columns and 'Inflation_Sentiment' in history_df.columns:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig2.add_trace(
            go.Scatter(x=history_df['Timestamp'], y=history_df['SPY'], name="SPY Price", line=dict(color='blue')),
            secondary_y=False,
        )
        
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
    
    if history_df is not None:
        price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
        avail_cols = [c for c in price_cols if c in history_df.columns]
        
        if len(avail_cols) > 1:
            clean_prices = history_df[avail_cols].dropna(axis=1, how='all')
            corr_matrix = clean_prices.pct_change().corr()
            
            fig3 = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
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
    
    if history_df is not None:
        # Hide price columns and the smoothed sentiment line
        price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
        
        # Filter out the rogue timestamp columns (anything containing "2026-")
        # We also keep out the price cols
        display_cols = [col for col in history_df.columns 
                        if col not in price_cols 
                        and col != 'Smoothed_Sentiment'
                        and not col.startswith('202')]
        
        priority_cols = ['Timestamp', 'Regime_V2', 'ML_Crash_Veto', 'VIX_Index', 'Real_Liquidity', 'Inflation_Sentiment']
        
        # Order the columns so the most important ones are on the left
        ordered_cols = [c for c in priority_cols if c in display_cols] + [c for c in display_cols if c not in priority_cols]
        
        st.dataframe(history_df[ordered_cols].tail(50).iloc[::-1], width='stretch')