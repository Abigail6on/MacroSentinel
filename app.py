import streamlit as st
import pandas as pd
import json
import os
from PIL import Image
import plotly.express as px

# --- PATH MANAGEMENT ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGIME_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
RISK_PATH = os.path.join(BASE_DIR, "data", "processed", "risk_metrics.json")
PERFORMANCE_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
DASHBOARD_IMG_PATH = os.path.join(BASE_DIR, "output", "sentinel_pro_dashboard.png")

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="MacroSentinel | Global Macro AI", layout="wide")

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
    ml_status = "Unknown"
    df = None
    if os.path.exists(REGIME_PATH):
        df = pd.read_csv(REGIME_PATH, index_col=0)
        latest_regime = df['Regime_V2'].iloc[-1]
        ml_veto = df['ML_Crash_Veto'].iloc[-1]
        ml_status = "CRASH IMMINENT (DEFENSIVE)" if ml_veto else "STANDBY (MARKET SAFE)"
        
    perf_df = None
    if os.path.exists(PERFORMANCE_PATH):
        perf_df = pd.read_csv(PERFORMANCE_PATH, index_col=0, parse_dates=True)
        
    return risk_data, latest_regime, ml_status, df, perf_df

risk_data, latest_regime, ml_status, history_df, perf_df = load_data()

# --- ROW 1: EXECUTIVE KPIs ---
st.markdown("### Real-Time System Status")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Current Market Regime", latest_regime)
col2.metric("ML Predictive Veto", ml_status)
col3.metric("Value at Risk (95%)", f"{risk_data.get('VaR_95', 'N/A')}%")
col4.metric("Expected Shortfall (CVaR)", f"{risk_data.get('CVaR_95', 'N/A')}%")

st.divider()

# --- ROW 2: INTERACTIVE EQUITY CURVE (PLOTLY) ---
st.markdown("### Interactive Performance Tracker")
if perf_df is not None:
    chart_data = perf_df[['Strategy_Value', 'Benchmark_Value']].rename(
        columns={'Strategy_Value': 'MacroSentinel AI', 'Benchmark_Value': 'SPY Benchmark'}
    )
    
    # Plotly automatically scales the Y-Axis for financial data
    fig = px.line(
        chart_data, 
        y=chart_data.columns,
        color_discrete_sequence=["#1f77b4", "#7f7f7f"] # Professional Blue and Grey
    )
    fig.update_layout(
        yaxis_title="Cumulative Return",
        xaxis_title="Date",
        legend_title="Portfolio",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Performance data not found. Please run the backtest engine.")

st.divider()

# --- ROW 3: VISUAL DASHBOARD ---
st.markdown("### Global Asset Allocation & NLP Sentiment Maps")
if os.path.exists(DASHBOARD_IMG_PATH):
    image = Image.open(DASHBOARD_IMG_PATH)
    st.image(image, use_container_width=True)
else:
    st.warning("Dashboard image not found.")

st.divider()

# --- ROW 4: RAW DATA INSPECTOR (DYNAMIC FILTER) ---
st.markdown("### Under the Hood: AI Decision Log")
st.caption("A streamlined view of the engine's core indicators (asset prices hidden for readability).")

if history_df is not None:
    # Dynamically drop raw stock prices so the table focuses only on macro/NLP logic
    price_cols = ['SPY', 'QQQ', 'GLD', 'SHY', 'XLF', 'XLU', 'XLE', 'TLT', 'DBC', 'EFA', 'EEM']
    display_cols = [col for col in history_df.columns if col not in price_cols]
    
    # Reorder to put the most important columns first
    priority_cols = ['Regime_V2', 'ML_Crash_Veto', 'Real_Liquidity']
    final_cols = priority_cols + [c for c in display_cols if c not in priority_cols]
    
    clean_df = history_df[final_cols].tail(10).iloc[::-1]
    st.dataframe(clean_df, use_container_width=True)
else:
    st.info("No historical data available yet.")