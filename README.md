# MacroSentinel: Sentiment-Driven Regime Engine

MacroSentinel is a quantitative framework designed to protect capital and generate alpha by fusing **"Hard"** economic indicators (FRED) with **"Soft"** alternative data (Real-time News Sentiment).

---

## 📈 Executive Performance Dashboard

![Sentinel Pro Dashboard](output/sentinel_pro_dashboard.png)
_Dashboard Components: (1) Regime-Aware Equity Curve, (2) Strategic Drawdown Analysis, (3) Risk/Fuel Driver Overlay._

---

## ⚙️ The "Capital Protection" Strategy

The model uses a **Triple-Veto** system to determine asset exposure:

| Component          | Logic                                                          | Goal                 |
| :----------------- | :------------------------------------------------------------- | :------------------- |
| **Regime Engine**  | Classifies Growth vs. Recession via News Sentiment.            | Directional Bias     |
| **Liquidity Veto** | Vetoes any "Buy" signal if M2 Money Supply growth < Inflation. | Avoid Bull Traps     |
| **VIX Governor**   | Automatically cuts stock exposure by 50% if VIX > 20.          | Volatility Targeting |

### **Current Asset Allocation**

- **Growth (Goldilocks):** 60% QQQ, 40% SPY
- **Neutral/Crisis:** 100% SHY (Cash/Short-term Bonds)
- **Overbought:** 60% SHY, 20% QQQ, 20% SPY

---

## 🛠️ System Architecture

1. **Indicator Harvesters:** Real-time collectors for FRED indicators (CPI, M2, Fed Funds, VIX).
2. **Sentiment Smoother:** Noise-reduction engine transforming headlines into 6-hour trends.
3. **Regime Engine V2:** Maps macro indicators and sentiment into 5 market states.
4. **Performance Engine:** High-fidelity backtester with **Friction Cost** accounting.

---

## 📂 Development Log (The Quant Practice)

### **Session 1: The "Gold Drag" Fix**

- **Issue:** Negative Alpha caused by Gold (GLD) falling alongside stocks.
- **Solution:** Removed Gold from core strategy. Pivoted to "Cash is King" (100% SHY) for defense.
- **Result:** **Bleeding Stopped.** Portfolio value flatlined during volatility.

### **Session 2: The "Liquidity Eyes" Fix**

- **Issue:** Model was "blind" to the Federal Reserve (Real Liquidity stuck at 0.0).
- **Solution:** Integrated M2 Money Supply data to calculate M2 Growth vs. CPI.
- **Result:** Detected +1.76% liquidity tailwind.

---

## 🚀 Getting Started

```bash
# Update indicators & fetch M2 Liquidity
python src/data/fred_collector.py

# Run backtest with VIX Governor
python src/backtest/performance_engine.py

# Generate the Pro Dashboard
python src/visualization/sentinel_pro_dashboard.py
```
