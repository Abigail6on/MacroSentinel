import pandas as pd
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PORTFOLIO_OUTPUT = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")

# REGIME-TO-ASSET MAPPING (The Strategy)
# This is the "secret sauce" of the model.
ALLOCATION_MAP = {
    "Goldilocks (Growth)": {
        "Strategy": "Aggressive Growth",
        "Primary_ETF": "QQQ",
        "Allocation": {"QQQ": 0.70, "SPY": 0.20, "GLD": 0.05, "TLT": 0.05}
    },
    "Goldilocks -> Tightening (Warning)": {
        "Strategy": "Defensive Growth",
        "Primary_ETF": "SPY",
        "Allocation": {"QQQ": 0.30, "SPY": 0.40, "GLD": 0.15, "TLT": 0.15}
    },
    "Overheat (Inflationary)": {
        "Strategy": "Inflation Hedge",
        "Primary_ETF": "XLE",
        "Allocation": {"XLE": 0.40, "DBC": 0.30, "GLD": 0.20, "SPY": 0.10}
    },
    "Stagflation (High Risk)": {
        "Strategy": "Capital Preservation",
        "Primary_ETF": "GLD",
        "Allocation": {"GLD": 0.50, "XLU": 0.20, "TLT": 0.20, "CASH": 0.10}
    },
    "Deflationary Recession (Confirmed)": {
        "Strategy": "Flight to Safety",
        "Primary_ETF": "TLT",
        "Allocation": {"TLT": 0.60, "GLD": 0.20, "SHY": 0.10, "CASH": 0.10}
    },
    "Neutral / Transitioning": {
        "Strategy": "Balanced",
        "Primary_ETF": "SPY",
        "Allocation": {"SPY": 0.40, "QQQ": 0.20, "TLT": 0.20, "GLD": 0.20}
    }
}

def generate_allocation():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] No regime data found. Run the Engine V2 first.")
        return

    # 1. Load latest status
    df = pd.read_csv(REGIME_DATA)
    latest_regime = df['Regime_V2'].iloc[-1]
    
    # 2. Map to Allocation
    config = ALLOCATION_MAP.get(latest_regime, ALLOCATION_MAP["Neutral / Transitioning"])
    
    print("\n--- TACTICAL ALLOCATOR REPORT ---")
    print(f"Current Regime:  {latest_regime}")
    print(f"Target Strategy: {config['Strategy']}")
    print(f"Top Conviction:  {config['Primary_ETF']}")
    print("---------------------------------")
    print("Asset Allocation Weights:")
    for ticker, weight in config['Allocation'].items():
        print(f"  {ticker}: {weight*100:.0f}%")

    # 3. Save for Dashboard/Backtester
    allocation_df = pd.DataFrame(list(config['Allocation'].items()), columns=['Ticker', 'Weight'])
    allocation_df['Regime'] = latest_regime
    allocation_df['Strategy'] = config['Strategy']
    allocation_df.to_csv(PORTFOLIO_OUTPUT, index=False)
    print(f"\n[SUCCESS] Target allocation saved to {PORTFOLIO_OUTPUT}")

if __name__ == "__main__":
    generate_allocation()