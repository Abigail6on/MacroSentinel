import pandas as pd
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
PORTFOLIO_OUTPUT = os.path.join(BASE_DIR, "data", "processed", "target_allocation.csv")

# Static Allocation Map for non-dynamic regimes
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

# Sector Rotation Thresholds
STEEP_THRESHOLD = 0.70  # Bullish for XLF
FLAT_THRESHOLD = 0.40   # Bullish for XLU

def generate_allocation():
    if not os.path.exists(REGIME_DATA):
        print("[ERROR] No regime data found. Run the Regime Engine first.")
        return

    # 1. Load latest market state
    df = pd.read_csv(REGIME_DATA)
    latest_row = df.iloc[-1]
    latest_regime = latest_row['Regime_V2']
    yield_curve = latest_row['Yield_Curve_10Y2Y']
    
    # 2. Dynamic Allocation Logic
    if latest_regime == "Goldilocks (Growth)":
        if yield_curve > STEEP_THRESHOLD:
            config = {
                "Strategy": "Growth + XLF Tilt (Steep Curve)",
                "Primary_ETF": "XLF",
                "Allocation": {"QQQ": 0.50, "SPY": 0.30, "XLF": 0.20}
            }
        elif yield_curve < FLAT_THRESHOLD:
            config = {
                "Strategy": "Growth + XLU Tilt (Flat Curve)",
                "Primary_ETF": "XLU",
                "Allocation": {"QQQ": 0.50, "SPY": 0.30, "XLU": 0.20}
            }
        else:
            config = {
                "Strategy": "Pure Growth (Neutral Curve)",
                "Primary_ETF": "QQQ",
                "Allocation": {"QQQ": 0.60, "SPY": 0.40}
            }
    else:
        # Fallback to static mapping for other regimes
        config = ALLOCATION_MAP.get(latest_regime, ALLOCATION_MAP["Neutral / Transitioning"])
    
    # 3. Terminal Reporting
    print("\n" + "="*45)
    print(" 🛡️  TACTICAL ALLOCATOR REPORT")
    print("="*45)
    print(f"Current Regime:  {latest_regime}")
    print(f"Yield Curve:     {yield_curve:.2f}")
    print(f"Target Strategy: {config['Strategy']}")
    print(f"Top Conviction:  {config['Primary_ETF']}")
    print("-" * 45)
    print("Final Portfolio Weights:")
    
    output_rows = []
    for ticker, weight in config['Allocation'].items():
        print(f"  {ticker.ljust(5)}: {weight*100:>3.0f}%")
        output_rows.append({
            "Ticker": ticker,
            "Weight": weight,
            "Regime": latest_regime,
            "Strategy": config['Strategy']
        })

    # 4. Persistence
    pd.DataFrame(output_rows).to_csv(PORTFOLIO_OUTPUT, index=False)
    print("="*45)
    print(f"[SUCCESS] Target saved to: {PORTFOLIO_OUTPUT}\n")

if __name__ == "__main__":
    generate_allocation()