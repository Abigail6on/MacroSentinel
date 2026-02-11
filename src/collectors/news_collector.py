import os
import requests
import pandas as pd
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Setup
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()

# Macro Categories: Broad economic focus
CATEGORIES = {
    "Economy": "economy OR 'interest rates' OR inflation",
    "Tech": "technology OR semiconductors OR AI",
    "Energy": "oil OR energy OR 'natural gas'"
}

def fetch_news_sentiment():
    if not NEWS_API_KEY:
        print("[ERROR] No NEWS_API_KEY found in .env file.")
        return

    print("[INFO] Initializing News Sentiment Collector...")
    results = []

    for category, query in CATEGORIES.items():
        print(f"[FETCHING] {category} headlines...")
        
        # Requesting 20 recent articles per category
        url = (f"https://newsapi.org/v2/everything?"
               f"q={query}&"
               f"language=en&"
               f"sortBy=publishedAt&"
               f"pageSize=20&"
               f"apiKey={NEWS_API_KEY}")
        
        try:
            response = requests.get(url)
            data = response.json()

            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                for art in articles:
                    # Combine title and description for a better sentiment score
                    text = f"{art.get('title', '')} {art.get('description', '')}"
                    score = analyzer.polarity_scores(text)['compound']
                    
                    results.append({
                        'Date': art.get('publishedAt'),
                        'Category': category,
                        'Sentiment': score,
                        'Title': art.get('title')
                    })
            else:
                print(f"[ERROR] API Response: {data.get('message')}")
        except Exception as e:
            print(f"[ERROR] Failed to connect: {e}")

    if results:
        df = pd.DataFrame(results)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Save raw news data
        output_path = "../../data/raw/news_sentiment_raw.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"[SUCCESS] News data saved to {output_path}")
        print(f"[STATS] Captured {len(df)} headlines.")
    else:
        print("[WARNING] No news items were collected.")

if __name__ == "__main__":
    fetch_news_sentiment()