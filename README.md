# MacroSentinel: Sentiment-Driven Regime Engine

MacroSentinel is a quantitative framework designed to protect capital and generate alpha by fusing **"Hard"** economic indicators (FRED macro data) with **"Soft"** alternative data (VADER NLP Real-time News Sentiment).

The system utilizes Mean-Variance Optimization, Walk-Forward Validation, and Institutional Circuit Breakers to dynamically adapt to shifting market regimes.

---

## 📈 Executive Performance Dashboard

![Sentinel Pro Dashboard](output/sentinel_pro_dashboard.png)
_Dashboard Components: (1) Regime-Aware Equity Curve, (2) Strategic Drawdown Analysis, (3) Risk/Fuel Driver Overlay._

---

## ⚙️ The Quantitative Framework

The model utilizes a **Multi-Factor Hierarchy** to determine tactical asset exposure:

| Component                   | Logic                                                                                       | Objective                   |
| :-------------------------- | :------------------------------------------------------------------------------------------ | :-------------------------- |
| **Regime Engine (NLP)**     | Classifies Growth vs. Neutral states using VADER Intensity-Weighted News Sentiment.         | Directional Bias            |
| **Mean-Variance Optimizer** | Dynamically weights the covariance matrix of QQQ, SPY, XLF, and XLU using SciPy `minimize`. | Maximize Sharpe/Smooth Ride |
| **Liquidity Veto**          | Vetoes "Buy" signals if M2 Money Supply growth < Inflation.                                 | Mitigate Bull Traps         |
| **VIX Governor**            | Reduces equity exposure by 50% when the VIX Index > 20.                                     | Volatility Targeting        |
| **Circuit Breaker**         | Emergency liquidation to Cash (SHY) if strategy equity drops ≥5% from High-Water Mark.      | Path-Dependent Protection   |

### **Dynamic Asset Allocation**

- **Growth (Goldilocks):** Dynamically optimized minimum-variance blend of `[QQQ, SPY, XLF, XLU]`
- **Neutral / Defensive:** 100% `[SHY]` (Short-term Treasuries)
- **Tactical Trim (VIX > 20):** Volatility-adjusted 50% equity reduction.

---

## 🛠️ System Architecture

1. **Indicator Harvesters:** Real-time collectors for FRED indicators (CPI, M2, Fed Funds, VIX).
2. **Sentiment Smoother:** VADER NLP engine calculating an Intensity Multiplier for market headlines.
3. **Regime Engine V2:** Fuses smoothed sentiment and liquidity into a unified market state.
4. **Walk-Forward Performance Engine:** Eliminates Look-Ahead Bias by rolling a 30-period in-sample optimization window to execute on $t+1$ out-of-sample returns.

---

## 🚀 Getting Started

```bash
# 1. Update macro indicators and fetch M2 Liquidity
python src/collectors/fred_collector.py
python src/collectors/news_collector.py

# 2. Process NLP Sentiment
python src/engine/sentiment_smoother.py

# 3. Analyze Market Regime
python src/engine/regime_engine_v2.py

# 4. Run Walk-Forward Out-of-Sample Backtest
python src/backtest/performance_engine.py

# 5. Generate the Professional Dashboard
python src/visualization/sentinel_pro_dashboard.py
```
