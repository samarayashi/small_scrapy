from scraper.spiders.cna.cna_menu_scraper import CnaMenuScraper
from scraper.spiders.cna.cna_spider import CnaSpider
from app.etl.news_pipeline import NewsETLPipeline
from app.database.connection import db_manager
from scraper.utils.logger import setup_logger
from line_broker.broker import NotificationBroker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings  # 需確保設定檔路徑正確
from app.main import create_app

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
        # 確保資料庫已初始化
        if not db_manager.engine:
            if not settings.database_url:
                raise ValueError("未設置資料庫連接字串 (DATABASE_URL)")
            db_manager.init_with_url(settings.database_url)
            
        # 確保資料表存在
        db_manager.create_tables()
        logger.info("資料表檢查完成")
        
        # 執行ETL流程
        pipeline = NewsETLPipeline()
        categories = ['acul', 'aie', 'ait']
        for category in categories:
            pipeline.spider.category = category
            pipeline.run()
        
    except Exception as e:
        logger.error(f"ETL執行失敗: {str(e)}")
        raise

def send_notifications(weather_only=False, news_only=False):
    """發送LINE通知"""
    try:
        # 驗證必要設定
        if not settings.database_url:
            raise ValueError("未設置資料庫連接字串 (DATABASE_URL)")
        if not settings.line_channel_token:
            raise ValueError("未設置 LINE Channel Access Token")
        
        # 建立資料庫連線
        engine = create_engine(settings.database_url, echo=settings.sql_echo)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 初始化通知代理
        broker = NotificationBroker(
            db_session=session,
            line_token=settings.line_channel_token,
            owm_api_key=settings.owm_api_key
        )
        
        # 根據參數決定發送通知類型
        if weather_only:
            if not settings.owm_api_key:
                raise ValueError("未設置 OpenWeatherMap API Key")
            broker.send_weather_notifications()
        elif news_only:
            broker.send_news_notifications()
        else:
            if settings.owm_api_key:
                broker.send_weather_notifications()
            broker.send_news_notifications()
            
        logger.info("通知發送流程完成")
        
    except Exception as e:
        logger.error(f"通知發送失敗: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    import argparse  # 新增argparse套件
    
    # 初始化參數解析器
    parser = argparse.ArgumentParser(description='中央社新聞處理系統')
    subparsers = parser.add_subparsers(dest='command', help='可用指令')
    
    # menu指令
    menu_parser = subparsers.add_parser('menu', help='更新類別配置')
    
    # news指令
    news_parser = subparsers.add_parser('news', help='測試新聞爬蟲')
    
    # etl指令
    etl_parser = subparsers.add_parser('etl', help='執行ETL流程')
    
    # notify指令
    notify_parser = subparsers.add_parser('notify', help='發送LINE通知')
    notify_group = notify_parser.add_mutually_exclusive_group()
    notify_group.add_argument('--weather-only', action='store_true', help='僅發送天氣通知')
    notify_group.add_argument('--news-only', action='store_true', help='僅發送新聞通知')
    
    # webhook指令
    webhook_parser = subparsers.add_parser('webhook', help='啟動Webhook伺服器')
    webhook_parser.add_argument('--port', type=int, default=5001, help='伺服器端口')
    webhook_parser.add_argument('--host', type=str, default='0.0.0.0', help='綁定主機')
    
    # 解析參數
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    try:
        if args.command == 'menu':
            update_menu_config()
        elif args.command == 'news':
            test_news_scraper()
        elif args.command == 'etl':
            run_etl()
        elif args.command == 'notify':
            send_notifications(
                weather_only=args.weather_only,
                news_only=args.news_only
            )
        elif args.command == 'webhook':
            app = create_app()
            app.run(host=args.host, port=args.port)
        else:
            logger.error(f"未知的命令: {args.command}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"執行失敗: {str(e)}")
        sys.exit(1) 