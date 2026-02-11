import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Environment-Agnostic Path Management
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
STREAM_PATH = os.path.join(BASE_DIR, "data", "raw", "news_stream_history.csv")

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()

# Expanded Precise Economic Indicators
INDICATOR_QUERIES = {
    "Monetary_Policy": "('Federal Reserve' OR 'interest rates') AND (hawkish OR dovish OR pivot)",
    "Labor_Market": "('unemployment' OR 'layoffs' OR 'hiring') AND economy",
    "Manufacturing": "('PMI' OR 'supply chain' OR 'industrial production') AND factory",
    "Inflation_Sentiment": "('CPI' OR 'cost of living' OR 'price increase') AND (anxiety OR surge OR crisis)"
}

def fetch_indicator_stream():
    if not NEWS_API_KEY:
        print("[ERROR] NEWS_API_KEY missing from environment.")
        return

    print(f"[INFO] Pumping indicator stream at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    new_results = []

    for label, query in INDICATOR_QUERIES.items():
        # Fetching top 15 relevant articles per indicator
        url = (f"https://newsapi.org/v2/everything?q={query}&"
               f"language=en&sortBy=publishedAt&pageSize=15&apiKey={NEWS_API_KEY}")
        
        try:
            response = requests.get(url)
            data = response.json()
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                for art in articles:
                    text = f"{art.get('title', '')} {art.get('description', '')}"
                    sentiment = analyzer.polarity_scores(text)['compound']
                    new_results.append({
                        'Timestamp': datetime.now(),
                        'Published_At': art.get('publishedAt'),
                        'Indicator': label,
                        'Sentiment': sentiment,
                        'Headline': art.get('title')
                    })
        except Exception as e:
            print(f"[ERROR] Connection failed for {label}: {e}")

    if new_results:
        new_df = pd.DataFrame(new_results)
        os.makedirs(os.path.dirname(STREAM_PATH), exist_ok=True)
        
        if not os.path.exists(STREAM_PATH):
            new_df.to_csv(STREAM_PATH, index=False)
        else:
            new_df.to_csv(STREAM_PATH, mode='a', header=False, index=False)
        print(f"[SUCCESS] Appended {len(new_results)} records to {STREAM_PATH}")

if __name__ == "__main__":
    fetch_indicator_stream()