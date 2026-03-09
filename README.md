# MacroSentinel: AI-Driven Global Macro Regime Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://macrosentinel-kgaeiagprtfjwfbjnav7dn.streamlit.app/)

**MacroSentinel** is an automated quantitative trading architecture built as a proof-of-concept for downside risk management and capital preservation. It fuses **"Hard"** economic indicators (FRED macro data), **"Soft"** alternative data (VADER NLP Real-Time News Sentiment), and **"Smart Money"** derivatives (Options Market Put/Call Ratios) and routes them through a Machine Learning Regime Engine.

The system utilizes XGBoost Predictive Modeling, SHAP Explainable AI, Mean-Variance Optimization, Walk-Forward Validation, and automated CI/CD cloud deployment to dynamically adapt to shifting global market regimes.

### Executive Summary (Business Impact)

- **The Problem:** Traditional rule-based trading bots react to market crashes _after_ they happen, leading to severe capital drawdown.
- **The Solution:** An autonomous, end-to-end MLOps pipeline that uses **Natural Language Processing** to read global financial news and an **XGBoost** machine learning brain to actively predict stock market drops 5 periods in advance.
- **The Result:** If the AI detects an impending crash, it triggers a defensive circuit breaker, reallocating the portfolio into safe-haven assets (Bonds/Cash). The frontend acts as an Interactive Risk Simulator, allowing users to dynamically calculate **Value at Risk (VaR)** and **Conditional VaR (CVaR)** to mathematically prove tail-risk downside protection, all while running fully automated in the cloud via **GitHub Actions**.

---

### Technical Stack

- **Data Engineering:** `pandas`, `numpy`, `yfinance`, `fredapi`, `vaderSentiment`
- **Machine Learning Engine:** `scikit-learn` (Random Forest), `xgboost` (Champion Model)
- **Model Interpretability:** `shap` (SHapley Additive exPlanations)
- **Quantitative Finance:** `scipy` (Optimization), `statsmodels` (Fama-French Factor Regression)
- **Visualization:** `matplotlib`, `seaborn`, `plotly`, `streamlit`

---

### Key Features

- **Explainable AI (SHAP):** Real-time JSON API payload generation that mathematically breaks down exactly _why_ the XGBoost model made its crash prediction, rendered as an interactive UI waterfall chart.
- **Options Market Sentiment:** Real-time S&P 500 Put/Call Open Interest ratio tracking institutional hedging and market panic via `yfinance`.
- **Dynamic Regime Detection:** Fuses 10Y-2Y Yield Curve Inversions, Real Liquidity (M2 Growth - CPI), and NLP Sentiment into a singular Market State.
- **Automated Rebalancing:** Adjusts portfolio weights using a Max Sharpe Ratio optimizer constrained by the live ML Regime.

---

## Live Interactive Dashboard

The frontend is hosted on Streamlit Community Cloud, providing a real-time window into the AI's decision-making process, active market regime, and current risk metrics. It includes a "State Override" feature to simulate portfolio behavior under forced economic stress tests.

**[👉 Click here to view the live Web App](https://macrosentinel-kgaeiagprtfjwfbjnav7dn.streamlit.app/)**

---

## 📈 Executive Performance

![Sentinel Pro Dashboard](output/sentinel_pro_dashboard.png)
_Dashboard Components: (1) Regime-Aware Equity Curve, (2) Strategic Target Allocation, (3) Risk/Fuel Driver Overlay (Real Liquidity), (4) NLP Sentiment Heatmap._

---

## ⚙️ The Quantitative Framework

The model utilizes a **Multi-Factor Hierarchy** to determine tactical global asset exposure across an 11-asset universe (`SPY, QQQ, GLD, SHY, XLF, XLU, XLE, TLT, DBC, EFA, EEM`):

| Component                   | Logic                                                                                                      | Objective                        |
| :-------------------------- | :--------------------------------------------------------------------------------------------------------- | :------------------------------- |
| **ML Predictive Veto**      | `XGBoost Classifier` trained on historical macro/NLP data to predict market drops.                         | Proactive Crash Evasion          |
| **Regime Engine V2**        | Fuses smoothed NLP sentiment, RSI momentum, and M2 Liquidity. Overridden by the ML Brain if needed.        | Directional Bias & State Mapping |
| **Global Asset Allocation** | Dynamically weights a covariance matrix using SciPy `minimize` with a strict 40% maximum position cap.     | Maximize Sharpe / Global Yield   |
| **Liquidity & VIX Vetoes**  | Sells equities for Cash/Bonds if Real M2 Money Supply < 0 or if the Global VIX spikes > 20.                | Systemic Risk Mitigation         |
| **Walk-Forward Engine**     | Eliminates Look-Ahead Bias by rolling a 30-period in-sample optimization window for out-of-sample returns. | Robust Strategy Validation       |
| **Risk Analytics**          | Computes dynamically adjustable Historical VaR and Expected Shortfall on out-of-sample returns.            | Tail-Risk Quantification         |

---

## 🛠️ System Architecture (End-to-End MLOps)

The system is fully automated via GitHub Actions, running a continuous data pipeline that seamlessly syncs the backend engine with the frontend web app.

1. **Data Ingestion:** Real-time collectors for FRED macro indicators, live global asset prices, and VADER NLP news sentiment.
2. **Model Training:** Trains the AI brain chronologically to avoid look-ahead bias and calculates the active market regime.
3. **Optimization & Risk:** Allocates the portfolio, runs the walk-forward backtest, computes VaR/CVaR, and executes Fama-French regressions.
4. **The "Data Bridge":** A GitHub Actions bot automatically commits the fresh AI predictions (`.csv`, `.json`) back to the repository.
5. **Continuous Deployment:** Streamlit Cloud detects the new commit and instantly updates the live public dashboard without human intervention.

---

## Getting Started (Local Runbook)

To run the full pipeline locally:

```bash
# 1. Ingest Data
python src/collectors/fred_collector.py
python src/collectors/options_collector.py
python src/collectors/news_collector.py
python src/portfolio/price_tracker.py

# 2. Process NLP Sentiment
python src/engine/sentiment_smoother.py

# 3. Train AI & Analyze Market Regime
python src/engine/ml_predictor.py
python src/engine/regime_engine_v2.py

# 4. Optimize Portfolio & Run Backtest
python src/portfolio/allocator.py
python src/backtest/performance_engine.py

# 5. Generate Risk Analytics, Attribution & Dashboard
python src/portfolio/risk_manager.py
python src/portfolio/factor_attribution.py
python src/visualization/sentinel_pro_dashboard.py

# 6. Launch the Local Web App
streamlit run app.py
```
