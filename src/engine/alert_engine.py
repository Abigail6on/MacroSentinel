import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REGIME_PATH = os.path.join(BASE_DIR, "data", "processed", "regime_v2_status.csv")
RISK_PATH = os.path.join(BASE_DIR, "data", "processed", "risk_metrics.json")

def send_discord_alert():
    print("--- Initializing Sentinel Alert Engine ---")
    
    if not WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL not found. Did you save it in your .env file?")
        return

    # Read the latest AI predictions and risk metrics
    try:
        regime_df = pd.read_csv(REGIME_PATH)
        latest_data = regime_df.iloc[-1]
        regime_name = latest_data.get("Regime_V2", "Unknown")
        ml_veto = latest_data.get("ML_Crash_Veto", False)
        
        with open(RISK_PATH, "r") as f:
            risk_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load data: {e}")
        return

    # Dynamic Alert Formatting (Red for Crash, Green for Safe)
    if ml_veto or regime_name in ["Defensive (Contraction)", "Stagflation / Liquidity Trap"]:
        embed_color = 16711680  # Bright Red
        title = "🚨 MACROSENTINEL: CRASH VETO ACTIVATED 🚨"
        description = "The XGBoost engine has detected severe downside risk and initiated a defensive portfolio rotation to Cash (SHY) & Safe Havens."
        ping = "@everyone"
    else:
        embed_color = 65280  # Bright Green
        title = "🟢 MACROSENTINEL: DAILY STATUS REPORT"
        description = "All systems nominal. XGBoost engine indicates stable market conditions."
        ping = ""

    # Build the JSON Payload for Discord
    embed = {
        "title": title,
        "description": description,
        "color": embed_color,
        "fields": [
            {
                "name": "📊 Current Market Regime",
                "value": f"**{regime_name}**",
                "inline": False
            },
            {
                "name": "📉 Risk Metrics",
                "value": f"**VaR (95%):** {risk_data.get('VaR_95', 'N/A')}\n**Max Drawdown:** {risk_data.get('Max_Drawdown', 'N/A')}",
                "inline": False
            }
        ],
        "footer": {
            "text": "MacroSentinel AI | Institutional Real-Time Risk Engine"
        }
    }

    payload = {
        "content": ping,
        "embeds": [embed]
    }

    # Fire the Webhook over the internet
    print("[INFO] Firing webhook to Discord...")
    response = requests.post(WEBHOOK_URL, json=payload)
    
    if response.status_code in [200, 204]:
        print("[SUCCESS] Alert sent to Discord successfully! Check your server.")
    else:
        print(f"[ERROR] Failed to send alert. Discord API responded with: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    send_discord_alert()