# 🛡️ MacroSentinel: Sentiment-Driven Regime Engine

MacroSentinel is a quantitative framework designed to protect capital and generate alpha by fusing **"Hard"** economic indicators (FRED) with **"Soft"** alternative data (Real-time News Sentiment).

The system dynamically rotates assets between Tech (QQQ), S&P 500 (SPY), Gold (GLD), and Cash/Bonds (SHY) based on market regimes and a **Liquidity Veto**.

---

## 📊 Live Performance Stats

| Metric               | Strategy (Macro Sentinel) | S&P 500 (Benchmark)  |
| :------------------- | :------------------------ | :------------------- |
| **Total Return (%)** | _Awaiting First Run_      | _Awaiting First Run_ |
| **Net Alpha**        | **0.00%**                 | --                   |
| **Status**           | 🛡️ Defensive              | --                   |

_Last Updated: 2026-02-18_

> **Note on Strategy Upgrade:** Following Phase C analysis, the model has been upgraded to a **"Cash is King"** defensive posture. During market instability, the engine now exits Gold (GLD) and moves 100% into Short-Term Treasuries (SHY) to prevent "insurance drag."

---

## 📈 Real-Time Analysis

### **Strategic Dashboard**

![Macro Dashboard](output/macro_dashboard_light.png)
_Regenerated hourly. Visualizes the Economic Pulse (Labor vs. Mfg), Inflation trends, and Tactical RSI levels._

### **Performance Attribution**

![Performance Dashboard](output/performance_dashboard.png)
_X-rays the portfolio to show exactly which assets are contributing to gains or causing losses._

---

## ⚙️ The "Stop Bleeding" Strategy

The model classifies the market into 5 distinct states:

| Regime                  | Asset Allocation          | Logic                                |
| :---------------------- | :------------------------ | :----------------------------------- |
| **Goldilocks (Growth)** | 50% QQQ, 30% SPY, 20% GLD | High growth, low inflation.          |
| **Overbought (Trim)**   | 20% QQQ, 20% SPY, 60% SHY | RSI > 70. Locking in profits.        |
| **Oversold (Buy)**      | 70% QQQ, 30% SPY          | RSI < 30. Aggressive entry.          |
| **Neutral (Defensive)** | **100% SHY (Cash)**       | Weakening macro. Zero risk.          |
| **Liquidity Crunch**    | **100% SHY (Cash)**       | Fed draining money. Exit all assets. |

---

## 🛠️ System Architecture

1. **Indicator Harvesters:** Real-time collectors for FRED indicators and Global News APIs.
2. **Sentiment Smoother:** Transforms volatile headlines into actionable 6-hour trends.
3. **Regime Engine V2:** Uses **Liquidity Veto** logic to override growth signals when the money supply is contracting.
4. **Performance Engine:** High-fidelity backtester that calculates Alpha and Max Drawdown.
5. **Auto-Reporter:** Injects live P&L data directly into this README via GitHub Actions.

---

## 🚀 Getting Started

### **Installation**

```bash
# 1. Clone the repo
git clone [https://github.com/your-username/MacroSentinel.git](https://github.com/your-username/MacroSentinel.git)
cd MacroSentinel

# 2. Setup environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

MacroSentinel/
├── .github/workflows/ # Automation Logic (GitHub Actions)
├── data/ # Raw FRED data & Processed Regimes
├── src/
│ ├── engine/ # Macro Logic & Liquidity Veto
│ ├── backtest/ # Performance Engine & Alpha tracking
│ └── visualization/ # P&L Attribution & README injection
└── output/ # Live Charts (Light Mode)
