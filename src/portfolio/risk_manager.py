import pandas as pd
import numpy as np
import os
import json

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
PERFORMANCE_REPORT = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
RISK_METRICS_OUT = os.path.join(BASE_DIR, "data", "processed", "risk_metrics.json")

def calculate_risk_metrics(confidence_level=0.95):
    print("--- Track 8: Institutional Risk Analytics ---")
    
    if not os.path.exists(PERFORMANCE_REPORT):
        print("[ERROR] Backtest data not found. Cannot calculate VaR.")
        return

    df = pd.read_csv(PERFORMANCE_REPORT)
    
    # Reconstruct the strategy returns from the equity curve
    df['Strat_Ret'] = df['Strategy_Value'].pct_change().fillna(0)
    returns = df['Strat_Ret'].values
    
    if len(returns) < 10:
        print("[WARNING] Not enough historical data to calculate reliable VaR.")
        return

    # 1. Historical Value at Risk (VaR)
    # If confidence is 95%, we find the 5th percentile of worst returns
    percentile = (1 - confidence_level) * 100
    historical_var = np.percentile(returns, percentile)

    # 2. Conditional VaR (Expected Shortfall)
    # The average of all returns that fall beyond the VaR threshold
    tail_losses = returns[returns <= historical_var]
    cvar = tail_losses.mean() if len(tail_losses) > 0 else historical_var

    # 3. Maximum Drawdown (Peak to Trough loss)
    running_max = np.maximum.accumulate(df['Strategy_Value'])
    drawdown = (df['Strategy_Value'] / running_max) - 1
    max_drawdown = drawdown.min()

    print(f"\n📊 Risk Assessment (Confidence: {confidence_level*100:.0f}%)")
    print(f"  -> Value at Risk (VaR):          {historical_var * 100:^7.2f}% (Max expected loss in normal conditions)")
    print(f"  -> Expected Shortfall (CVaR):    {cvar * 100:^7.2f}% (Average loss during a tail-risk crash)")
    print(f"  -> Maximum Historical Drawdown:  {max_drawdown * 100:^7.2f}%")

    # Save to a JSON file so our future Web App can easily read it
    risk_data = {
        "VaR_95": round(historical_var * 100, 3),
        "CVaR_95": round(cvar * 100, 3),
        "Max_Drawdown": round(max_drawdown * 100, 3)
    }
    
    with open(RISK_METRICS_OUT, "w") as f:
        json.dump(risk_data, f, indent=4)
        
    print(f"\n[SUCCESS] Risk metrics saved to {RISK_METRICS_OUT}")

if __name__ == "__main__":
    calculate_risk_metrics()