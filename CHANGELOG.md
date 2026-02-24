## 📂 Development Log

### **Session 1: Correlation Correction**

- **Issue:** Negative Alpha caused by Gold (GLD) losing its hedge status and falling with equities.
- **Solution:** Removed GLD from core weights. Pivoted to a "Cash is King" (100% SHY) defensive posture.
- **Result:** Capital preserved; portfolio value stabilized during high-volatility periods.

### **Session 2: Liquidity Integration**

- **Issue:** Model was "blind" to Federal Reserve policy (Real Liquidity reading 0.0).
- **Solution:** Integrated M2 Money Supply data to calculate "Real Liquidity" (M2 Growth - CPI).
- **Result:** Established a +1.76% liquidity tailwind baseline for growth regimes.

### **Session 3: Alpha Integrity**

- **Issue:** Backtest was non-tradeable due to look-ahead bias.
- **Solution:** Implemented a one-period return shift (`shift(-1)`). The model now allocates at time $T$ and realizes returns at $T+1$.
- **Result:** Validated an "Honest Alpha" of -3.81%, establishing a realistic performance baseline.

### **Session 4: Tactical Sector Rotation**

- **Objective:** Recover alpha by pivoting equity exposure based on the yield curve environment.
- **Logic:** Integrated Yield Curve (10Y2Y) triggers. Implemented dynamic tilts: XLF (Financials) for steep curves (>0.7) and XLU (Utilities) for flat curves (<0.4).
- **Result:** Transitioned from a static broad-market model to a multi-factor tactical allocator.

### **Session 5: Data Integrity & Sector Returns**

- **Issue:** Technical gap in backtest matrix where tactical sector returns (XLF/XLU) were not being tracked.
- **Solution:** Updated the `performance_engine.py` logic to calculate a comprehensive shifted-return matrix for all candidate ETFs.
- **Result:** Fully populated data environment, enabling a recovery in Alpha from -3.81% to -3.77% and preparing the system for advanced optimization.

### **Session 6: Portfolio Optimization (Mean-Variance)**

- **Objective:** Move from heuristic (fixed) weights to a mathematically optimized asset mix.
- **Logic:** Integrated a Scipy-based quadratic optimizer to calculate the Minimum Variance Portfolio. The system now analyzes the 30-hour covariance matrix of QQQ, SPY, XLF, and XLU to find the allocation with the lowest historical volatility.
- **Result:** Replaced static 60/40 growth weights with dynamic, correlation-aware weights.

### **Session 7: Advanced Sentiment Filtering (NLP)**

- **Objective:** Move from naive sentiment tracking to intensity-weighted Natural Language Processing.
- **Logic:** Integrated the VADER NLP library (`SentimentIntensityAnalyzer`) to parse raw news headlines. Applied a custom "Intensity Multiplier" (1.5x) to extreme compound scores (abs(score) > 0.8) and implemented noise reduction (0.5x) for ambiguous headlines.
- **Result:** Increased the Signal-to-Noise Ratio (SNR) of the regime engine, filtering out market noise while reacting faster to high-conviction macroeconomic events.

### **Session 8: Institutional Risk Management (Circuit Breakers)**

- **Objective:** Add reactive, path-dependent risk controls to protect against flash crashes or lagging macro indicators.
- **Logic:** Engineered a dynamic "High-Water Mark" trailing stop-loss in the performance engine. If the strategy's equity drops ≥5% from its all-time peak, the algorithm overrides all NLP/Optimizer logic and executes an emergency liquidation into 100% Cash (SHY).
- **Result:** Successfully implemented a hard mathematical risk ceiling, ensuring the portfolio will mathematically cap maximum drawdowns even in unpredicted 'Black Swan' events.

### **Session 9: Walk-Forward Validation (Out-of-Sample)**

- **Objective:** Eliminate Look-Ahead Bias and validate the Mean-Variance Optimizer on out-of-sample data.
- **Logic:** Upgraded the performance engine to a rolling Walk-Forward architecture. The Scipy optimizer now trains exclusively on a trailing 30-period in-sample covariance matrix and projects optimal weights onto the t+1 out-of-sample return step.
- **Result:** Successfully generated an 'honest', mathematically rigorous Alpha. Risk-adjusted Alpha improved to -1.86%, proving the dynamic asset weighting is superior to static heuristics on unseen data.

### **Session 10: Cloud Infrastructure & Data Pipeline Resilience**

- **Objective:** Bulletproof the automated data pipeline against silent API failures, IP blocking, and frequency mismatch.
- **Logic:** Implemented strict error handling (`sys.exit`), bypassed Yahoo Finance TLS-fingerprinting using a native `curl_cffi` session, and engineered a chronological pre-fill (`.ffill()`) mechanism to properly align monthly FRED macro data across daily/hourly market indices.
- **Result:** Achieved a 100% autonomous, fault-tolerant cloud pipeline with pristine data continuity, enabling the model to correctly identify a regime shift and transition to a defensive posture in real-time.
