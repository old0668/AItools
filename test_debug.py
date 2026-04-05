import yaml
import os
import logging
from core.ingestion import Ingestor
from core.processing import Processor
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def load_config(config_path='config/config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test():
    config = load_config()
    ingestor = Ingestor(config['news_sources'])
    raw_news = ingestor.fetch_all()
    
    with open('data/last_pub_time.txt', 'r') as f:
        last_pub = f.read().strip()
        print(f"Current last_pub_time in file: {last_pub}")
        last_pub_dt = datetime.fromisoformat(last_pub)

    print("\nAnalyzing specific item that has keywords:")
    for item in raw_news:
        if "川普" in item['title']:
            print(f"Title: {item['title']}")
            print(f"Published: {item['published']}")
            # Simulate parsing logic
            import dateutil.parser
            pub_dt = dateutil.parser.parse(item['published'])
            if pub_dt.tzinfo:
                pub_dt = pub_dt.astimezone().replace(tzinfo=None)
            else:
                pub_dt = pub_dt.replace(tzinfo=None)
            print(f"Parsed DT: {pub_dt.isoformat()}")
            print(f"Is Parsed DT > Last Pub? {pub_dt > last_pub_dt}")
            print("-" * 20)
            break

if __name__ == "__main__":
    test()
