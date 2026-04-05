import yaml
import os
import logging
from core.ingestion import Ingestor
from core.processing import Processor
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path='config/config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test():
    config = load_config()
    
    print("\n--- Testing Ingestion ---")
    ingestor = Ingestor(config['news_sources'])
    raw_news = ingestor.fetch_all()
    print(f"Total raw news fetched: {len(raw_news)}")
    
    if len(raw_news) > 0:
        print(f"Example raw item: {raw_news[0]['title']} ({raw_news[0]['published']})")

    print("\n--- Testing Processing ---")
    # Temporary check: bypass the last_pub_time filter by removing the file or using a fresh Processor
    if os.path.exists('data/last_pub_time.txt'):
        with open('data/last_pub_time.txt', 'r') as f:
            print(f"Current last_pub_time: {f.read().strip()}")
    
    processor = Processor(config['keywords'], config['llm'])
    
    # We can manually inspect what's happening in filter_by_keywords
    filtered_news = processor.filter_by_keywords(raw_news)
    print(f"News after filtering: {len(filtered_news)}")
    
    if len(filtered_news) > 0:
        for i, item in enumerate(filtered_news[:5]):
            print(f"{i+1}. [{item.get('display_time')}] {item['title']}")
    else:
        print("No news passed the filters.")
        # Let's see why. Check a few items against keywords.
        print("\nChecking first 5 items against keywords:")
        for item in raw_news[:5]:
            content = (item.get('title', '') + " " + item.get('summary', '')).lower()
            matches = [kw for kw in config['keywords'] if kw.lower() in content]
            print(f"Title: {item['title']}")
            print(f"Matches: {matches}")
            print("-" * 20)

if __name__ == "__main__":
    test()
