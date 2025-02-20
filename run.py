from scraper.spiders.cna.cna_menu_scraper import CnaMenuScraper
from scraper.spiders.cna.cna_spider import CnaSpider
from app.etl.news_pipeline import NewsETLPipeline
from app.database.connection import db_manager
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_menu_config():
    """更新類別配置文件"""
    scraper = CnaMenuScraper()
    menu_mapping = scraper.get_menu_mapping(force_update=True)
    print("類別對應表:")
    for code, name in menu_mapping.items():
        print(f"{code}: {name}")

def test_news_scraper():
    """測試新聞爬蟲"""
    spider = CnaSpider(category='asoc')
    for article in spider.crawl():
        print(article)

def run_etl():
    """執行ETL流程"""
    try:
        # 確保資料表存在
        db_manager.create_tables()
        logger.info("資料表檢查完成")
        
        # 執行ETL流程
        pipeline = NewsETLPipeline()
        pipeline.run()
        
    except Exception as e:
        logger.error(f"ETL執行失敗: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("請指定要執行的功能：")
        print("python run.py menu  # 更新選單配置")
        print("python run.py news  # 測試新聞爬蟲")
        print("python run.py etl   # 執行ETL流程")
        sys.exit(1)
    
    command = sys.argv[1]
    if command == "menu":
        update_menu_config()
    elif command == "news":
        test_news_scraper()
    elif command == "etl":
        run_etl()
    else:
        print(f"未知的命令: {command}") 