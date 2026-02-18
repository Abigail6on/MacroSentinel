import pandas as pd
import os

# Path Management
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_PATH = os.path.join(BASE_DIR, "data", "processed", "backtest_results.csv")
README_PATH = os.path.join(BASE_DIR, "README.md")

def update_readme():
    if not os.path.exists(RESULTS_PATH): return
    df = pd.read_csv(RESULTS_PATH)
    
    # 1. Calculate Metrics
    strat_ret = (df['Strategy_Value'].iloc[-1] - 1) * 100
    bench_ret = (df['Benchmark_Value'].iloc[-1] - 1) * 100
    alpha = strat_ret - bench_ret
    
    # Check asset drag (specifically Gold)
    gld_perf = ((1 + df['GLD_Ret'].fillna(0)).cumprod().iloc[-1] - 1) * 100
    gld_warning = "⚠️" if gld_perf < -2.0 else "✅"

    # 2. Build Markdown Table
    table_content = [
        "\n### 📊 Live Performance Stats\n",
        "| Metric | Strategy | S&P 500 |\n",
        "| :--- | :--- | :--- |\n",
        f"| **Total Return** | {strat_ret:+.2f}% | {bench_ret:+.2f}% |\n",
        f"| **Net Alpha** | **{alpha:+.2f}%** | -- |\n",
        f"| **Gold Health** | {gld_perf:+.2f}% {gld_warning} | -- |\n\n",
        f"*Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*\n"
    ]

    # 3. Inject into README
    with open(README_PATH, 'r') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    for line in lines:
        if "" in line:
            new_lines.append(line)
            new_lines.extend(table_content)
            skip = True
        elif "" in line:
            new_lines.append(line)
            skip = False
        elif not skip:
            new_lines.append(line)

    with open(README_PATH, 'w') as f:
        f.writelines(new_lines)
    print("[SUCCESS] README stats updated.")

if __name__ == "__main__":
    update_readme()