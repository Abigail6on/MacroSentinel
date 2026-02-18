import pandas as pd
import os
import re

# Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RESULTS_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
README_PATH = os.path.join(BASE_DIR, "README.md")

def update_readme():
    if not os.path.exists(RESULTS_PATH) or not os.path.exists(README_PATH):
        print("[ERROR] Files missing.")
        return

    df = pd.read_csv(RESULTS_PATH)
    
    # 1. Calculate Metrics
    strat_ret = (df['Strategy_Value'].iloc[-1] - 1) * 100
    bench_ret = (df['Benchmark_Value'].iloc[-1] - 1) * 100
    alpha = strat_ret - bench_ret
    
    gld_perf = ((1 + df['GLD_Ret'].fillna(0)).cumprod().iloc[-1] - 1) * 100
    gld_warning = "⚠️" if gld_perf < -2.0 else "✅"

    # 2. Build the New Markdown Table
    new_table = (
        f"| Metric | Strategy | S&P 500 |\n"
        f"| :--- | :--- | :--- |\n"
        f"| **Total Return** | {strat_ret:+.2f}% | {bench_ret:+.2f}% |\n"
        f"| **Net Alpha** | **{alpha:+.2f}%** | -- |\n"
        f"| **Gold Health** | {gld_perf:+.2f}% {gld_warning} | -- |\n\n"
        f"*Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*"
    )

    # 3. Read and Replace using Regex
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # This regex looks for the START and END markers and captures everything in between
    pattern = r"()(.*?)()"
    
    # We replace the middle part (group 2) with our new table
    replacement = f"\\1\n{new_table}\n\\3"
    
    # re.DOTALL is critical: it tells Python that the '.' should match newlines too
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_content)
        
    print("[SUCCESS] README cleaned and updated with fresh stats.")

if __name__ == "__main__":
    update_readme()