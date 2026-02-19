import pandas as pd
import numpy as np
from scipy.optimize import minimize
import os

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_DATA = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")

def get_optimal_growth_weights():
    """
    Calculates weights for the growth assets that minimize total portfolio variance.
    """
    if not os.path.exists(REGIME_DATA):
        return {"QQQ": 0.6, "SPY": 0.4} # Fallback

    df = pd.read_csv(REGIME_DATA)
    # We use the last 30 periods to capture recent volatility regimes
    assets = ["QQQ", "SPY", "XLF", "XLU"]
    available_assets = [a for a in assets if a in df.columns]
    
    # Calculate returns
    returns = df[available_assets].pct_change().dropna().tail(30)
    
    if len(returns) < 10:
        return {"QQQ": 0.6, "SPY": 0.4}

    # Covariance Matrix
    cov_matrix = returns.cov().values
    
    # Optimization Function: Minimize Variance
    def portfolio_variance(weights):
        return np.dot(weights.T, np.dot(cov_matrix, weights))

    # Constraints: Weights must sum to 1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # Bounds: No short selling (0 to 1 per asset)
    bounds = tuple((0, 1) for _ in range(len(available_assets)))
    # Initial guess: Equal weights
    init_guess = [1.0/len(available_assets)] * len(available_assets)

    optimized = minimize(portfolio_variance, init_guess, 
                         method='SLSQP', bounds=bounds, constraints=constraints)
    
    if not optimized.success:
        return {"QQQ": 0.6, "SPY": 0.4}

    # Return as a clean dictionary
    return dict(zip(available_assets, np.round(optimized.x, 2)))

if __name__ == "__main__":
    weights = get_optimal_growth_weights()
    print("Optimization Complete. Optimal Growth Mix:")
    for t, w in weights.items():
        print(f"  {t}: {w*100:.0f}%")