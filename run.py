from scraper.spiders.cna.cna_menu_scraper import CnaMenuScraper
from scraper.spiders.cna.cna_spider import CnaSpider
from app.etl.news_pipeline import NewsETLPipeline
from app.database.connection import db_manager
from scraper.utils.logger import setup_logger

# 設置日誌
logger = setup_logger(__name__)



def update_menu_config():
    """更新類別配置文件"""
    try:
        scraper = CnaMenuScraper()
        menu_mapping = scraper.get_menu_mapping(force_update=True)
        logger.info("類別對應表:")
        for code, name in menu_mapping.items():
            logger.info(f"{code}: {name}")
    except Exception as e:
        logger.error(f"更新選單配置失敗: {str(e)}")
        raise

def test_news_scraper():
    """測試新聞爬蟲"""
    try:
        spider = CnaSpider(category='asoc')
        for article in spider.crawl():
            logger.info(article)
    except Exception as e:
        logger.error(f"新聞爬取測試失敗: {str(e)}")
        raise

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
        logger.error("請指定要執行的功能：")
        logger.info("python run.py menu  # 更新選單配置")
        logger.info("python run.py news  # 測試新聞爬蟲")
        logger.info("python run.py etl   # 執行ETL流程")
        sys.exit(1)
    
    command = sys.argv[1]
    try:
        if command == "menu":
            update_menu_config()
        elif command == "news":
            test_news_scraper()
        elif command == "etl":
            run_etl()
        else:
            logger.error(f"未知的命令: {command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"執行失敗: {str(e)}")
        sys.exit(1) 