from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import scoped_session
from app.database.connection import db_manager
from scraper.spiders.cna.cna_spider import CnaSpider
from line_broker.broker import NotificationBroker
from app.config.settings import settings
from scraper.utils.logger import setup_logger
# 使用自定義的logger設置
logger = setup_logger(__name__)

# 全局實例，確保只有一個排程器
scheduler = None

class SchedulerService:
    def __init__(self, app=None):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.session_factory = None
        
        if app is not None:
            self.init_app(app)
        
        # 設置全局實例
        global scheduler
        scheduler = self.scheduler
        
    def init_app(self, app):
        """延遲初始化模式"""
        self.app = app
        self._init_db_session()
            
    def _init_db_session(self):
        """初始化資料庫會話"""
        self.session_factory = scoped_session(db_manager.session_factory)

    def _get_db_session(self):
        """獲取資料庫會話"""
        if self.session_factory is None:
            self._init_db_session()
        return self.session_factory()

    def _crawl_job(self):
        """排程任務：執行新聞爬蟲並存入資料庫"""
        session = self._get_db_session()
        try:
            # 爬取所有訂閱類別的新聞
            categories = ['acul', 'aie', 'ait']  # 可從資料庫動態獲取
            # categories = session.query(SubNews.news_category_key).distinct().all()
            for category in categories:
                spider = CnaSpider(category=category)
                for article in spider.crawl():
                    # 這裡需實作將文章存入資料庫的邏輯
                    logger.info(f"爬取到文章: {article.title}")
        except Exception as e:
            logger.error(f"排程任務執行失敗: {str(e)}")
        finally:
            session.close()
    
    def _notify_weather(self):
        """排程任務：執行天氣通知"""
        logger.info("開始執行天氣通知任務")
        session = self._get_db_session()
        
        try:
            # 創建通知代理實例
            broker = NotificationBroker(
                db_session=session,
                line_token=settings.line_channel_token,
                owm_api_key=settings.owm_api_key
            )
            
            # 使用代理發送天氣通知
            broker.send_weather_notifications()
            
        except Exception as e:
            logger.error(f"天氣通知任務執行失敗: {str(e)}")
        finally:
            # 正確的會話清理順序
            session.close()  # 首先關閉特定會話
            self.session_factory.remove()  # 然後清理線程本地存儲
            logger.info("天氣通知任務完成")
        
    def start(self):
        """啟動排程器"""
        # 每天早上八點執行新聞爬蟲
        self.scheduler.add_job(
            self._crawl_job,
            trigger=CronTrigger(hour=8, minute=0),
            max_instances=1
        )
        
        # 每天早上八點執行天氣通知
        self.scheduler.add_job(
            self._notify_weather,
            trigger=CronTrigger(hour=8, minute=0),
            max_instances=1
        )
        
        # 添加一個測試任務，用於開發階段測試（每分鐘執行一次）
        if self.app and settings.scheduler_debug:
            self.scheduler.add_job(
                self._notify_weather,
                trigger=CronTrigger(second='*/10'),  # 每10秒執行一次，用於測試
                max_instances=1,
                id='weather_test_job'
            )
            logger.info("已添加天氣通知測試任務（每分鐘執行）")
        
        self.scheduler.start()
        logger.info("排程服務已啟動")

    def shutdown(self):
        """關閉排程器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("排程服務已關閉") 