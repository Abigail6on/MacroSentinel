# 🛡️ MacroSentinel: Sentiment-Driven Regime Engine

MacroSentinel is a quantitative framework designed to protect capital and generate alpha by fusing **"Hard"** economic indicators (FRED) with **"Soft"** alternative data (Real-time News Sentiment).

The system dynamically rotates assets between Tech (QQQ), S&P 500 (SPY), Gold (GLD), and Cash/Bonds (SHY) based on market regimes and a **Liquidity Veto**.

---

## 📈 Real-Time Analysis

### **Strategic Dashboard**

![Macro Dashboard](output/macro_sentinel_dashboard.png)
_Regenerated hourly. Visualizes the Economic Pulse (Labor vs. Mfg), Inflation trends, and Tactical RSI levels._

### **Performance Comparison**

![Performance Dashboard](output/performance_dashboard.png)
_Visualizes the equity curve and Alpha generation relative to the S&P 500 benchmark._

---

## ⚙️ The "Capital Protection" Strategy

The model classifies the market into 5 distinct states to determine asset exposure:

| Regime                  | Asset Allocation          | Logic                               |
| :---------------------- | :------------------------ | :---------------------------------- |
| **Goldilocks (Growth)** | 50% QQQ, 30% SPY, 20% GLD | High growth, low inflation.         |
| **Overbought (Trim)**   | 20% QQQ, 20% SPY, 60% SHY | RSI > 70. Locking in profits.       |
| **Oversold (Buy)**      | 70% QQQ, 30% SPY          | RSI < 30. Aggressive entry.         |
| **Neutral (Defensive)** | 100% SHY (Cash)           | Weakening macro. Zero risk mandate. |
| **Liquidity Crunch**    | 100% SHY (Cash)           | Fed draining money. Systemic exit.  |

---

## 🛠️ System Architecture

1. **Indicator Harvesters:** Real-time collectors for FRED indicators and Global News APIs.
2. **Sentiment Smoother:** Transforms volatile headlines into actionable 6-hour trends.
3. **Regime Engine V2:** Uses **Liquidity Veto** logic to override growth signals when the money supply is contracting.
4. **Performance Engine:** High-fidelity backtester that calculates Alpha and Max Drawdown.

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
