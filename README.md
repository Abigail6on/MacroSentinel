# MacroSentinel: Real-Time Multi-Asset Regime Engine

MacroSentinel is a quantitative framework designed to detect macroeconomic "weather" patterns and dynamically rotate assets between Tech, Energy, Gold, and Bonds.

The system combines "Hard" economic data (via FRED API) with "Soft" alternative data (Real-time Indicator News Stream) to classify the market into four regimes: Goldilocks, Overheat, Stagflation, and Recession.

## 🚀 The Development Journey

### Phase 1: The Prototype (Completed)

- **Architecture:** Static data pipeline fetching 50 years of FRED macro indicators.
- **Discovery:** Identified a significant time-horizon mismatch between monthly economic reports and 24-hour news sentiment.
- **Result:** Established the baseline 4-quadrant classification logic.

### Phase 2: Pivot to Real-Time Sentinel (In Progress)

- **Precision Indicators:** Moving from general "Economy" news to specific signals (Fed Policy, Labor Market Pulse, Manufacturing PMI).
- **Streaming Engine:** Implementing an append-only data stream to build a proprietary sentiment history.
- **Sentiment Smoothing:** Applying rolling averages to convert noisy headline spikes into actionable trend signals.

## 🛠️ System Architecture

1. **Collectors:** Multi-threaded harvesters for FRED and NewsAPI.
2. **Engine:** Hidden Markov Model (HMM) logic for regime classification.
3. **Allocator:** Dynamic Risk-Parity weighting based on detected "Weather."
4. **Dashboard:** Streamlit-based UI for real-time monitoring.

## 📈 Current Technical Stack

- **Language:** Python 3.12
- **Data:** Pandas, NumPy, FredAPI, NewsAPI
- **ML/Analytics:** Scikit-learn, VADER Sentiment, FinBERT (Planned)
- **Deployment:** GitHub Actions (Planned for Streamer automation)
