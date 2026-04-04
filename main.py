#!/usr/bin/env python3
import asyncio
import yaml
import os
import logging
import platform
from dotenv import load_dotenv
from core.ingestion import Ingestor
from core.processing import Processor
from core.delivery import Notifier

# Load environment variables
if not os.path.exists('.env'):
    print("錯誤：找不到 .env 檔案！請將 .env.example 重新命名為 .env 並填入您的 API Key。")
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path='config/config.yaml'):
    # Ensure we use absolute paths if running from different directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_config_path = os.path.join(base_dir, config_path)
    with open(full_config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

async def run_aggregator():
    sys_type = platform.system()
    if sys_type in ["Darwin", "Windows"]:
        logger.info(f"檢測到 {sys_type} 環境，正在初始化...")
    
    logger.info("Starting News Aggregator Core Logic...")
    
    # 1. Load Configuration
    config = load_config()
    
    # 2. Ingestion
    ingestor = Ingestor(config['news_sources'])
    raw_news = ingestor.fetch_all()
    logger.info(f"Fetched {len(raw_news)} items from sources.")
    
    # 3. Processing
    processor = Processor(config['keywords'], config['llm'])
    filtered_news = processor.filter_by_keywords(raw_news)
    logger.info(f"Found {len(filtered_news)} items after filtering and deduplication.")
    
    # 4. Summarization
    # 注意：即便 filtered_news 為空，我們也呼叫 summarize，以便記錄「持平」的信心指數
    logger.info("Generating LLM summary (or recording flat trend)...")
    summary = processor.summarize(filtered_news)
    
    if summary is None:
        logger.info("No new news, trend recorded as flat.")
        return None, filtered_news

    # 5. Delivery
    notifier = Notifier()
    logger.info("Delivering summary to configured channels...")
    await notifier.notify_all(summary)
    
    return summary, filtered_news

async def main():
    summary, _ = await run_aggregator()
    print("\n--- Generated Summary ---\n")
    print(summary)
    print("\n-------------------------\n")
    
    if platform.system() == "Darwin":
        print("✅ 任務完成！已發送系統通知。")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n使用者中斷執行。")
