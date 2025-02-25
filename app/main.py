from flask import Flask
from app.database.connection import db_manager
from app.services.scheduler_service import SchedulerService
from line_broker.webhook_handler import webhook_blueprint
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

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
    scheduler = SchedulerService(app)
    scheduler.start()
    
    # 3. 註冊藍圖
    app.register_blueprint(webhook_blueprint)
    
    # 4. 添加關閉鉤子
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        scheduler.shutdown()
        logger.info("排程服務已關閉")

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001) 