import pandas as pd
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PORTFOLIO_OUTPUT = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")

# --- STEP 1: THE CASH PIVOT STRATEGY ---
# We have removed Gold from defensive regimes to "Stop the Bleeding."
ALLOCATION_MAP = {
    "Goldilocks (Growth)": {
        "Strategy": "Aggressive Growth",
        "Primary_ETF": "QQQ",
        "Allocation": {"QQQ": 0.60, "SPY": 0.40}
    },
    "Goldilocks (Overbought - Trim)": {
        "Strategy": "Tactical De-risking",
        "Primary_ETF": "SHY",
        "Allocation": {"SHY": 0.60, "QQQ": 0.20, "SPY": 0.20}
    },
    "Goldilocks (Oversold - Opportunity)": {
        "Strategy": "Aggressive Re-entry",
        "Primary_ETF": "QQQ",
        "Allocation": {"QQQ": 0.80, "SPY": 0.20}
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
        print("[ERROR] No regime data found. Run the Engine V2 first.")
        return

    # 1. Load latest status
    df = pd.read_csv(REGIME_DATA)
    latest_regime = df['Regime_V2'].iloc[-1]
    
    # 2. Map to Allocation (Fallback to Neutral if regime unknown)
    config = ALLOCATION_MAP.get(latest_regime, ALLOCATION_MAP["Neutral / Transitioning"])
    
    print("\n" + "="*40)
    print(" 🛡️  TACTICAL ALLOCATOR REPORT")
    print("="*40)
    print(f"Current Regime:  {latest_regime}")
    print(f"Target Strategy: {config['Strategy']}")
    print(f"Top Conviction:  {config['Primary_ETF']}")
    print("-" * 40)
    print("Final Portfolio Weights:")
    
    # 3. Prepare data for CSV
    output_rows = []
    for ticker, weight in config['Allocation'].items():
        print(f"  {ticker}: {weight*100:.0f}%")
        output_rows.append({
            "Ticker": ticker,
            "Weight": weight,
            "Regime": latest_regime,
            "Strategy": config['Strategy']
        })

    # 4. Save to CSV
    pd.DataFrame(output_rows).to_csv(PORTFOLIO_OUTPUT, index=False)
    print("="*40)
    print(f"[SUCCESS] Allocation saved to: {PORTFOLIO_OUTPUT}\n")

if __name__ == "__main__":
    generate_allocation()