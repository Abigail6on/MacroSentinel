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

# Static Allocation Map for Defensive and Transitional States
ALLOCATION_MAP = {
    "Goldilocks (Overbought - Trim)": {
        "Strategy": "Tactical De-risking",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 0.60, "QQQ": 0.20, "SPY": 0.20}
    },
    "Goldilocks (Oversold - Opportunity)": {
        "Strategy": "Aggressive Re-entry",
        "Primary_ETF": "QQQ",
        "Allocation": {"QQQ": 0.70, "SPY": 0.30}
    },
    "Neutral / Transitioning": {
        "Strategy": "Capital Preservation",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 1.0}
    },
    "Liquidity Crunch (Defensive)": {
        "Strategy": "Nuclear Safety",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 1.0}
    }
}

def generate_allocation():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] No regime data found. Ensure the regime engine has been executed.")
        return

    # 1. Load latest market state
    df = pd.read_csv(REGIME_DATA)
    latest_row = df.iloc[-1]
    latest_regime = latest_row['Regime_V2']
    
    # 2. Dynamic Allocation Logic via Optimization
    if latest_regime == "Goldilocks (Growth)":
        print("System State: Growth detected. Initializing Mean-Variance Optimizer...")
        # Call the optimizer to find the Minimum Variance mix of QQQ, SPY, XLF, and XLU
        opt_weights = get_optimal_growth_weights()
        
        config = {
            "Strategy": "Optimized Minimum Variance Growth",
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
    print(f"[SUCCESS] Strategic targets saved to: {PORTFOLIO_OUTPUT}\n")

if __name__ == "__main__":
    generate_allocation()