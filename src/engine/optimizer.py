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
    Calculates weights for the Global Growth assets that minimize total portfolio variance.
    """
    # UPGRADE: Expanded Global Risk-On Universe
    target_assets = ["SPY", "QQQ", "XLF", "XLU", "XLE", "EFA", "EEM"]
    
    if not os.path.exists(REGIME_DATA):
        return {"QQQ": 0.5, "SPY": 0.5} # Emergency Fallback

    df = pd.read_csv(REGIME_DATA)
    
    # Dynamically filter to assets that actually exist in the CSV to prevent KeyErrors
    available_assets = [a for a in target_assets if a in df.columns]
    
    if len(available_assets) == 0:
        return {"QQQ": 0.5, "SPY": 0.5}
        
    # Calculate returns using the trailing 30 hours
    returns = df[available_assets].pct_change().dropna().tail(30)
    
    # Dynamic Equal-Weight Fallback if data is too short
    if len(returns) < 10:
        return {a: 1.0/len(available_assets) for a in available_assets}

    # Covariance Matrix (The N x N Matrix)
    cov_matrix = returns.cov().values
    
    # Optimization Function: Minimize Variance
    def portfolio_variance(weights):
        return np.dot(weights.T, np.dot(cov_matrix, weights))

    # Constraints: Weights must sum to exactly 1.0 (100% Capital Deployed)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # UPGRADE (Risk Management): Cap any single asset at 40% maximum to force global diversification
    bounds = tuple((0.0, 0.40) for _ in range(len(available_assets)))
    
    # Initial guess: Equal weights
    init_guess = [1.0/len(available_assets)] * len(available_assets)

    optimized = minimize(portfolio_variance, init_guess, 
                         method='SLSQP', bounds=bounds, constraints=constraints)
    
    if not optimized.success:
        return {a: 1.0/len(available_assets) for a in available_assets}

    # Map optimized weights back to tickers, rounding to 4 decimals
    optimal_weights = {available_assets[i]: round(optimized.x[i], 4) for i in range(len(available_assets))}
    
    # Clean up near-zero weights (dust)
    return {k: v for k, v in optimal_weights.items() if v > 0.001}