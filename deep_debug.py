import yaml
import json
import os
import hashlib
from core.ingestion import Ingestor

def deep_debug():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 1. 檢查歷史紀錄
    history_file = 'data/history.json'
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        print(f"DEBUG: 歷史紀錄檔案存在，內容數量: {len(history)}")
    else:
        history = []
        print("DEBUG: 歷史紀錄檔案不存在 (已清除)")

    # 2. 抓取原始新聞
    ingestor = Ingestor(config['news_sources'])
    raw_news = ingestor.fetch_all()
    print(f"DEBUG: 抓取到原始新聞總數: {len(raw_news)}")

    if not raw_news:
        print("DEBUG: 🔴 錯誤！抓取結果為 0，RSS 來源可能拒絕連線。")
        return

    # 3. 模擬過濾邏輯
    keywords = config['keywords']
    keyword_fail = 0
    duplicate_fail = 0
    success = []

    for item in raw_news:
        title = item.get('title', '')
        summary = item.get('summary', '')
        link = item.get('link', '')
        content = (title + " " + summary).lower()
        
        # 關鍵字檢查
        matched_ks = [k for k in keywords if k.lower() in content]
        if not matched_ks:
            keyword_fail += 1
            continue
            
        # 重複檢查
        url_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
        if url_hash in history:
            duplicate_fail += 1
            continue
            
        success.append(item)

    print(f"DEBUG: 過濾統計:")
    print(f"  - 關鍵字不匹配: {keyword_fail}")
    print(f"  - 連結重複 (History): {duplicate_fail}")
    print(f"  - 通過過濾: {len(success)}")

    if success:
        print(f"DEBUG: 第一篇通過的文章標題: {success[0]['title']}")
    else:
        print("DEBUG: 🔴 最終沒有任何文章通過。")
        # 如果關鍵字全滅，印出第一篇內容供參考
        if keyword_fail > 0:
            print(f"DEBUG: 參考內容 (第一篇): {raw_news[0]['title']} | 摘要: {raw_news[0]['summary'][:100]}")

if __name__ == "__main__":
    deep_debug()
