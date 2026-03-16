# MacroSentinel: AI-Driven Global Macro Regime Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://macrosentinel-kgaeiagprtfjwfbjnav7dn.streamlit.app/)

**MacroSentinel** is an automated quantitative trading architecture built as a proof-of-concept for downside risk management and capital preservation. It fuses **"Hard"** economic indicators (FRED macro data), **"Soft"** alternative data (VADER NLP Real-Time News Sentiment), and **"Smart Money"** derivatives (Options Market Put/Call Ratios) and routes them through a Machine Learning Regime Engine.

The system utilizes a 13-factor XGBoost Predictive Model, SHAP Explainable AI, Mean-Variance Optimization, Walk-Forward Validation, and automated CI/CD cloud deployment to dynamically adapt to shifting global market regimes.

### Executive Summary (Business Impact)

- **The Problem:** Traditional rule-based trading bots react to market crashes _after_ they happen, leading to severe capital drawdown.
- **The Solution:** An autonomous, end-to-end MLOps pipeline that uses **Natural Language Processing** to read global financial news and an **XGBoost** machine learning brain to actively predict stock market drops 5 periods in advance.
- **The Result:** If the AI detects an impending crash, it triggers a defensive circuit breaker, reallocating the portfolio into safe-haven assets (Bonds/Cash). The frontend acts as an Interactive Risk Simulator, allowing users to dynamically calculate **Value at Risk (VaR)** and view real-time Alpha generation.

---

## The Master Dashboard

_(A real-time, 6-panel visualization of the AI's decision-making process, risk metrics, and alpha generation.)_

![MacroSentinel Dashboard](output/sentinel_pro_dashboard.png)

_(Note: If you have any other existing performance tables or charts in your current README, keep them right here!)_

---

## 🚀 Key Technical Features

### 1. Multivariate XGBoost Regime Engine

Unlike static rule-based bots, MacroSentinel relies on a dynamically trained **XGBoost Classifier** that ingests 13 time-series features (including Lag, Momentum, and Rolling Volatility). The AI actively predicts market drawdowns and triggers a defensive "ML Crash Veto."

### 2. Explainable AI (SHAP)

Black-box models are a liability in quantitative finance. This project implements a real-time **SHAP (SHapley Additive exPlanations)** explainer. The UI dynamically scales and visualizes the top driving factors behind every XGBoost prediction, proving exactly _why_ the model shifted its regime classification.

### 3. NLP Sentiment Alpha Generation

A real-time data pipeline scrapes global financial news, processes it through a VADER NLP sentiment analyzer, and smooths the signals. The engine correlates this textual data with quantitative asset pricing, proving that the model generates positive Alpha by acting on macroeconomic sentiment _before_ it is fully priced into the SPY benchmark.

### 4. Institutional-Grade Backtester

The performance engine goes beyond simple returns by incorporating:

- **Transaction Friction:** A dynamic 5 basis point (0.05%) penalty is applied to portfolio turnover during every rebalance to simulate real-world bid-ask spread slippage.
- **Risk Analytics:** Continuous calculation of Maximum Drawdown, Value at Risk (VaR), and Conditional Value at Risk (CVaR).

---

## System Architecture & MLOps Pipeline

This repository is fully automated using a Continuous Integration/Continuous Deployment (CI/CD) pipeline via GitHub Actions to sync the backend data with the frontend web app.

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
