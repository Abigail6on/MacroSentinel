# MacroSentinel: Real-Time Multi-Asset Regime Engine

MacroSentinel is a quantitative framework designed to detect macroeconomic "weather" patterns and dynamically rotate assets between Tech, Energy, Gold, and Bonds.

The system fuses "Hard" economic indicators (FRED) with "Soft" alternative data (Real-time News Sentiment) to classify the market into four distinct regimes.

## 📊 Real-Time Macro Dashboard

![Macro Sentinel Dashboard](output/macro_sentinel_dashboard.png)

_The dashboard is automatically regenerated every hour via GitHub Actions, integrating precise sentiment streams with systemic risk matrices._

---

## 🚀 The Development Journey

### Phase 1: The Prototype (Completed)

- **Architecture:** Static data pipeline fetching 50 years of FRED macro indicators.
- **Discovery:** Identified the "Lagging Signal" problem where monthly reports miss intra-month market pivots.
- **Result:** Established the baseline 4-quadrant classification logic.

### Phase 2: The Real-Time Sentinel (Operational)

- **Precision Indicators:** Developed targeted Boolean scrapers for Monetary Policy, Labor Market Pulse, and Industrial Production.
- **Automation:** Implemented a full CI/CD pipeline using **GitHub Actions** to build a proprietary sentiment history.
- **Signal Processing:** Integrated a **Sentiment Smoother** (Rolling Mean) and **Hysteresis Logic** to stabilize regime transitions and eliminate headline noise.

---

## 🛠️ System Architecture

1. **Indicator Harvesters:** Daily/Hourly collectors for FRED macro data and NewsAPI signals.
2. **Sentiment Smoother:** A noise-reduction engine that transforms volatile headlines into actionable trends.
3. **Regime Engine V2:** A hysteresis-aware classifier that merges monthly macro data with high-frequency sentiment.
4. **Visualizer:** A professional dashboard generator using Matplotlib and Seaborn for automated reporting.

---

## 📈 Technical Stack

- **Automation:** GitHub Actions (Full Pipeline Orchestration)
- **Data Science:** Pandas, NumPy, Scikit-learn
- **NLP:** VADER Sentiment Analysis
- **Visualization:** Matplotlib, Seaborn
- **Environment:** Python 3.12, Dotenv for API Security

---

## 📂 Project Structure

```text
MacroSentinel/
├── .github/workflows/  # Automation Logic
├── data/
│   ├── raw/            # Proprietary News History
│   └── processed/      # Smoothed Signals & Regime Status
├── src/
│   ├── collectors/     # Data Acquisition
│   ├── engine/         # Logic & Hysteresis Calibration
│   └── visualization/  # Dashboard Generation
└── output/             # Live Analytical Visuals
```
