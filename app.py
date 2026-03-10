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

risk_data, live_regime, live_veto, history_df, perf_df = load_data()

# Pre-calculate main return metrics if available
strat_ret = 0.0
spy_ret = 0.0
alpha_basis = 0.0

if perf_df is not None and not perf_df.empty and 'Strategy_Value' in perf_df.columns:
    strat_ret = (perf_df['Strategy_Value'].iloc[-1] - 1) * 100
    spy_ret = (perf_df['Benchmark_Value'].iloc[-1] - 1) * 100
    alpha_basis = perf_df['Alpha_Basis'].iloc[-1]

# --- INTERACTIVE SIDEBAR ---
with st.sidebar:
    st.header("Risk & Simulation Parameters")
    st.markdown("Interact with the model's risk tolerance and state.")
    
    # 1. The VaR Slider
    conf_level = st.slider("VaR Confidence Level (%)", min_value=90, max_value=99, value=95, step=1)
    
    st.divider()
    
    # 2. The Regime Override Dropdown
    st.subheader("State Override")
    st.caption("Temporarily override the live ML data to simulate portfolio behavior under different economic conditions.")
    regime_override = st.selectbox(
        "Force Market Regime", 
        ["Live Data", "Force: Goldilocks (Growth)", "Force: Defensive (Contraction)", "Force: Neutral / Transitioning"]
    )

# Apply the Override Logic
if regime_override != "Live Data":
    current_regime = regime_override.replace("Force: ", "")
    # Automatically trigger the ML Veto if they force a Defensive state
    is_veto_active = True if current_regime == "Defensive (Contraction)" else False
else:
    current_regime = live_regime
    is_veto_active = live_veto

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

# --- MAIN UI HEADER ---
st.title("MacroSentinel: AI-Driven Global Macro Fund")
st.markdown("An institutional quantitative framework fusing NLP Sentiment, Macroeconomic Data, and Machine Learning to dynamically navigate market regimes.")
if regime_override != "Live Data":
    st.warning(f"⚠️ SIMULATION MODE ACTIVE: Displaying simulated data for {current_regime}")
st.divider()

# --- UI TABS ---
tab1, tab2, tab3 = st.tabs(["Executive Summary", "Model Analytics & Logic", "Risk & Decision Log"])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    # UPDATED NET RETURNS
    col1.metric("Net Strategy Return", f"{strat_ret:.2f}%", f"{alpha_basis:.2f}% Net Alpha vs SPY")
    col2.metric("SPY Benchmark", f"{spy_ret:.2f}%")
    col3.metric("Max Drawdown", risk_data.get('Max_Drawdown', 'N/A'))
    col4.metric("Market Regime", current_regime)
    
    # DISCLAIMER ADDED HERE
    st.caption("ℹ️ **Quantitative Note:** Strategy returns are *Net of Fees*, incorporating a dynamic 5 basis point (0.05%) institutional slippage penalty applied to portfolio turnover during every rebalance.")

    st.divider()
    st.markdown("### Regime-Aware Performance Curve")
    if perf_df is not None and not perf_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=perf_df['Timestamp'], y=perf_df['Strategy_Value'], name='Sentinel Strategy (Net)', line=dict(color='#00ff00', width=2)))
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
    
    if history_df is not None and 'SPY' in history_df.columns and 'Inflation_Sentiment' in history_df.columns:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=history_df['Timestamp'], y=history_df['SPY'], name="SPY Price", line=dict(color='blue')), secondary_y=False)
        history_df['Smoothed_Sentiment'] = history_df['Inflation_Sentiment'].ffill().bfill().rolling(7, min_periods=1).mean()
        fig2.add_trace(go.Scatter(x=history_df['Timestamp'], y=history_df['Smoothed_Sentiment'], name="Rolling NLP Sentiment", line=dict(color='orange', dash='dot')), secondary_y=True)
        fig2.update_yaxes(title_text="<b>SPY Price</b>", secondary_y=False)
        fig2.update_yaxes(title_text="<b>News Sentiment (-1 to 1)</b>", secondary_y=True)
        fig2.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig2, width='stretch')
        
        # 💡 Institutional Tooltip
        with st.expander("How to interpret NLP Alpha"):
            st.write("This chart maps the S&P 500 against a 7-day rolling VADER sentiment score derived directly from real-time news APIs. Divergences (where the price rises but sentiment drops into the negative) act as leading indicators for the XGBoost engine to predict imminent market contractions.")
    
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
            
            # 💡 Institutional Tooltip
            with st.expander("How to interpret the Correlation Matrix"):
                st.write("Displays the rolling linear correlation between asset classes. During a market crash, correlations often move toward 1.0 (everything sells off together). The optimizer uses this matrix to find non-correlated safe havens, like Treasury Bonds (SHY) or Gold (GLD), to dynamically hedge the portfolio.")

# ==========================================
# TAB 3: RISK & DECISION LOG
# ==========================================
with tab3:
    st.markdown("### Global Asset Allocation & Risk Maps")
    if os.path.exists(DASHBOARD_IMG_PATH):
        image = Image.open(DASHBOARD_IMG_PATH)
        st.image(image)

    st.divider()
    st.markdown("### Under the Hood: AI Decision Log")
    if history_df is not None:
        price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
        display_cols = [col for col in history_df.columns if col not in price_cols and col != 'Smoothed_Sentiment' and not col.startswith('202')]
        priority_cols = ['Timestamp', 'Regime_V2', 'ML_Crash_Veto', 'VIX_Index', 'Real_Liquidity', 'Inflation_Sentiment']
        ordered_cols = [c for c in priority_cols if c in display_cols] + [c for c in display_cols if c not in priority_cols]
        st.dataframe(history_df[ordered_cols].tail(50).iloc[::-1], width='stretch')