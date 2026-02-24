import pandas as pd
import yfinance as yf
import statsmodels.api as sm
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
BACKTEST_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "output", "factor_attribution_summary.txt")

def run_factor_attribution():
    print("--- Running Fama-French 3-Factor Attribution ---")
    
    if not os.path.exists(BACKTEST_PATH):
        print("[ERROR] Backtest results not found. Run performance_engine.py first.")
        return
        
    df = pd.read_csv(BACKTEST_PATH)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    
    # 1. Resample Strategy to Daily Returns (End of Day)
    daily_strat = df['Strategy_Value'].resample('D').last().dropna()
    strat_returns = daily_strat.pct_change().dropna()
    
    # Strip the time so it is just the pure Date (YYYY-MM-DD)
    strat_returns.index = strat_returns.index.normalize()
    
    # 2. Fetch Proxy Factor Data (Daily)
    start_date = strat_returns.index.min()
    # Add a 2-day buffer to ensure we get the latest Yahoo data
    end_date = strat_returns.index.max() + pd.Timedelta(days=2) 
    
    tickers = ["SPY", "IWM", "VTV", "VUG"]
    print(f"Downloading Factor Proxy ETFs from {start_date.date()} to {end_date.date()}...")
    factors = yf.download(tickers, start=start_date, end=end_date, interval="1d")
    factors = factors['Close'] if isinstance(factors.columns, pd.MultiIndex) else factors
    
    # Clean YF index to match the strategy Date index
    factors.index = factors.index.tz_localize(None).normalize()
    
    # 3. Calculate Factor Returns
    factor_rets = factors.pct_change().dropna()
    
    factor_rets['MKT'] = factor_rets['SPY']
    factor_rets['SMB'] = factor_rets['IWM'] - factor_rets['SPY']
    factor_rets['HML'] = factor_rets['VTV'] - factor_rets['VUG']
    
    # 4. Align Data by Exact Date
    aligned_data = pd.concat([strat_returns.rename("Strategy"), factor_rets[['MKT', 'SMB', 'HML']]], axis=1).dropna()
    
    if aligned_data.empty:
        print("[ERROR] Aligned data is empty. Not enough overlapping daily data yet.")
        print("Wait 24 hours for the backtest to accumulate more daily closures.")
        return
        
    # 5. Run OLS Regression
    Y = aligned_data['Strategy']
    X = aligned_data[['MKT', 'SMB', 'HML']]
    X = sm.add_constant(X) # This calculates Alpha
    
    model = sm.OLS(Y, X).fit()
    summary_str = str(model.summary())
    
    print("\n[FACTOR ATTRIBUTION OLS RESULTS]")
    print(summary_str)
    
    # Extract True Alpha (Scaled up for 252 trading days)
    alpha_daily = model.params['const']
    alpha_annualized = alpha_daily * 252
    p_value = model.pvalues['const']
    
    analysis = (
        f"\n{'='*50}\n"
        f"🎯 KEY TAKEAWAYS FOR YOUR RESUME / INTERVIEW\n"
        f"{'='*50}\n"
        f"Annualized True Alpha (Intercept): {alpha_annualized * 100:.4f}%\n"
        f"Market Beta (Correlation to SPY):  {model.params['MKT']:.2f}\n"
    )
    
    if p_value < 0.05:
        analysis += f"Significance: HIGH (p={p_value:.4f}).\n-> Conclusion: Your strategy generates genuine alpha independent of market drift!\n"
    else:
        analysis += f"Significance: LOW (p={p_value:.4f}).\n-> Conclusion: Returns are largely explained by broader market movements (or needs more data points).\n"
        
    print(analysis)
    
    # 6. Save text file to output folder so GitHub Actions tracks it
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write("--- MacroSentinel Fama-French Factor Attribution ---\n\n")
        f.write(summary_str)
        f.write("\n")
        f.write(analysis)

if __name__ == "__main__":
    run_factor_attribution()