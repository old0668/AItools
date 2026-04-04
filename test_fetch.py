import yaml
import feedparser
import hashlib
import json
import os
from core.ingestion import Ingestor

def test_fetch():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if os.path.exists('data/history.json'):
        with open('data/history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    print(f"目前歷史記錄中有 {len(history)} 篇文章。")
    
    ingestor = Ingestor(config['news_sources'])
    raw_news = ingestor.fetch_all()
    print(f"從 RSS 來源共抓取到 {len(raw_news)} 篇文章。")
    
    keywords = config['keywords']
    new_and_matched = []
    
    for item in raw_news:
        url_hash = hashlib.md5(item['link'].encode('utf-8')).hexdigest()
        content = (item['title'] + " " + item['summary']).lower()
        
        is_new = url_hash not in history
        matches_keyword = any(k.lower() in content for k in keywords)
        
        if is_new and matches_keyword:
            new_and_matched.append(item)
        elif is_new:
            # Optionally print why it was filtered
            pass

    print(f"經過關鍵字與去重過濾後，剩餘 {len(new_and_matched)} 篇新文章。")
    if new_and_matched:
        for i, item in enumerate(new_and_matched[:3]):
            print(f"[{i+1}] {item['title']} ({item['published']})")
    else:
        print("結論：目前沒有符合關鍵字的新新聞。")

if __name__ == "__main__":
    test_fetch()
