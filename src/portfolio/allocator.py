import pandas as pd
import os
import sys

# Find the current directory (src/portfolio)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(SCRIPT_DIR)

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from engine.optimizer import get_optimal_growth_weights

# Path Management for Data
BASE_DIR = os.path.dirname(SRC_DIR)
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PORTFOLIO_OUTPUT = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")

# UPGRADED GLOBAL ALLOCATION MAP
ALLOCATION_MAP = {
    "Goldilocks (Overbought - Trim)": {
        "Strategy": "Tactical De-risking",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 0.50, "QQQ": 0.25, "SPY": 0.25}
    },
    "Goldilocks (Oversold - Opportunity)": {
        "Strategy": "Aggressive Re-entry",
        "Primary_ETF": "QQQ",
        "Allocation": {"QQQ": 0.60, "SPY": 0.20, "EFA": 0.10, "EEM": 0.10}
    },
    "Neutral / Transitioning": {
        "Strategy": "Capital Preservation",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 1.0}
    },
    "Defensive (Contraction)": {
        "Strategy": "Duration Hedging (Recession)",
        "Primary_ETF": "TLT",
        "Allocation": {"TLT": 0.60, "SHY": 0.40} # TLT rallies when rates drop
    },
    "Stagflation / Liquidity Trap": {
        "Strategy": "Hard Asset Protection",
        "Primary_ETF": "DBC",
        "Allocation": {"DBC": 0.50, "GLD": 0.30, "SHY": 0.20} # Commodities hedge inflation
    }
}

def generate_target_allocations():
    """Reads current regime and outputs a target portfolio weight map."""
    
    if not os.path.exists(REGIME_DATA):
        print(f"[ERROR] Missing regime data at {REGIME_DATA}")
        return
        
    df = pd.read_csv(REGIME_DATA)
    if df.empty:
        print("[ERROR] Regime data is empty.")
        return
        
    latest_regime = df['Regime_V2'].iloc[-1]
    
    # 1. Base Assignment
    if latest_regime == "Goldilocks (Growth)":
        # Call the optimizer to find the Minimum Variance mix of the GLOBAL universe
        opt_weights = get_optimal_growth_weights()
        
        config = {
            "Strategy": "Optimized Global Minimum Variance",
            "Primary_ETF": max(opt_weights, key=opt_weights.get),
            "Allocation": opt_weights
        }
    else:
        # Fallback to predefined strategic weights for non-growth states
        config = ALLOCATION_MAP.get(latest_regime, ALLOCATION_MAP["Neutral / Transitioning"])
    
    # 3. Terminal Reporting for Audit
    print("\n" + "="*45)
    print(" TACTICAL ALLOCATOR REPORT")
    print("="*45)
    print(f"Current Regime:  {latest_regime}")
    print(f"Target Strategy: {config['Strategy']}")
    print(f"Top Conviction:  {config['Primary_ETF']}")
    print("-" * 45)
    print("Final Portfolio Weights:")
    
    output_rows = []
    for ticker, weight in config['Allocation'].items():
        if weight > 0: # Only record active positions
            print(f"  {ticker.ljust(5)}: {weight*100:>3.0f}%")
            output_rows.append({
                "Ticker": ticker,
                "Weight": weight,
                "Regime": latest_regime,
                "Strategy": config['Strategy']
            })

    # 4. Persistence to CSV
    pd.DataFrame(output_rows).to_csv(PORTFOLIO_OUTPUT, index=False)
    print("="*45)

if __name__ == "__main__":
    generate_target_allocations()