from flask import Flask
from app.database.connection import db_manager
from app.services.scheduler_service import SchedulerService
from line_broker.webhook_handler import webhook_blueprint
from app.config.settings import settings
from scraper.utils.logger import setup_logger
import signal
import sys
import os

logger = setup_logger(__name__)

# 確保只創建一個排程器實例
scheduler_service = None

def create_app():
    """工廠模式創建Flask應用"""
    app = Flask(__name__)
    
    # 設置配置
    app.config.from_mapping(
        DATABASE_URL=settings.database_url,
        LINE_CHANNEL_TOKEN=settings.line_channel_token,
        LINE_CHANNEL_SECRET=settings.line_channel_secret
    )
    
    # 初始化組件
    _init_components(app)
    
    # 註冊 SIGTERM 處理器
    register_shutdown_handlers()
    
    return app

def _init_components(app):
    """初始化各項組件"""
    # 1. 資料庫初始化
    try:
        db_manager.init_app(app)
        logger.info("資料庫初始化完成")
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {str(e)}")
        raise
    
    # 2. 排程服務初始化
    global scheduler_service
    scheduler_service = SchedulerService(app)
    scheduler_service.start()
    
    # 3. 註冊藍圖，加上 /line 作為前綴
    app.register_blueprint(webhook_blueprint, url_prefix='/line')
    
    # 4. 添加關閉鉤子
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_manager.session_factory.remove()
        logger.info("資料庫會話已移除")

def register_shutdown_handlers():
    """註冊各種關閉信號的處理器"""
    
    def shutdown_scheduler():
        """關閉排程器"""
        try:
            global scheduler_service
            if scheduler_service:
                logger.info("關閉排程器...")
                scheduler_service.shutdown()
                return True
        except Exception as e:
            logger.error(f"關閉排程器時發生錯誤: {str(e)}")
        return False
    
    def shutdown_db():
        """關閉資料庫連接"""
        try:
            if db_manager and db_manager.session_factory:
                logger.info("關閉資料庫連接...")
                db_manager.session_factory.remove()
                return True
        except Exception as e:
            logger.error(f"關閉資料庫連接時發生錯誤: {str(e)}")
        return False
    
    def sigterm_handler(signum, frame):
        """處理 SIGTERM 信號"""
        logger.info("收到 SIGTERM 信號，開始優雅關閉...")
        
        # 按優先順序關閉各項資源
        shutdown_scheduler()
        shutdown_db()
        
        logger.info("應用程式已完成優雅關閉")
        sys.exit(0)
    
    # 註冊信號處理器
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.app_port))
    app = create_app()
    app.run(host='0.0.0.0', port=port) 