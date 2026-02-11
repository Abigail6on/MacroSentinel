import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Setup
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()
STREAM_PATH = "../../data/raw/news_stream_history.csv"

# Precise Economic Indicators: Boolean logic for signal isolation
INDICATOR_QUERIES = {
    "Monetary_Policy": "('Federal Reserve' OR 'interest rates') AND (hawkish OR dovish OR pivot)",
    "Labor_Market": "('unemployment' OR 'layoffs' OR 'hiring') AND economy",
    "Manufacturing": "('PMI' OR 'supply chain' OR 'industrial production') AND factory"
}

def fetch_indicator_stream():
    if not NEWS_API_KEY:
        print("[ERROR] NEWS_API_KEY missing from environment.")
        return

    print(f"[INFO] Pumping indicator stream at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    new_results = []

    for label, query in INDICATOR_QUERIES.items():
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
        # Append mode allows us to build a proprietary dataset over time
        if not os.path.exists(STREAM_PATH):
            new_df.to_csv(STREAM_PATH, index=False)
        else:
            new_df.to_csv(STREAM_PATH, mode='a', header=False, index=False)
        print(f"[SUCCESS] Appended {len(new_results)} records to stream history.")

if __name__ == "__main__":
    fetch_indicator_stream()