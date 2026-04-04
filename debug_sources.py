import yaml
import feedparser
import logging
import httpx
from core.ingestion import Ingestor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_each_source():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    sources = config['news_sources']
    keywords = config['keywords']
    
    print(f"--- 開始測試共 {len(sources)} 個新聞來源 ---\n")
    
    total_raw = 0
    for source in sources:
        print(f"正在檢查: {source['name']}...")
        try:
            # Use httpx to check if the URL is even reachable
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                resp = client.get(source['url'])
                print(f"  - HTTP 狀態碼: {resp.status_code}")
                print(f"  - 回傳內容長度: {len(resp.text)}")
                
                if len(resp.text) < 100:
                    print(f"  ⚠️ 警告: 回傳內容過短，可能被封鎖或參數錯誤。")
                
                feed = feedparser.parse(resp.text)
                items_count = len(feed.entries)
                print(f"  - 成功解析出 {items_count} 篇文章")
                total_raw += items_count
                
                if items_count > 0:
                    # Check first item and keyword matching
                    first_item = feed.entries[0]
                    content = (first_item.get('title', '') + " " + first_item.get('summary', '')).lower()
                    matched = [k for k in keywords if k.lower() in content]
                    print(f"  - 第一篇標題範例: {first_item.get('title', '無標題')[:50]}...")
                    print(f"  - 關鍵字匹配情況: {'✅ 匹配' if matched else '❌ 無匹配'} (符合: {matched if matched else '無'})")
                
        except Exception as e:
            print(f"  ❌ 發生錯誤: {e}")
        print("-" * 30)

    print(f"\n總結: 原始抓取總數 = {total_raw}")
    if total_raw == 0:
        print("🔴 嚴重錯誤: 所有來源皆未回傳內容！可能是網路問題或來源連結失效。")

if __name__ == "__main__":
    test_each_source()
