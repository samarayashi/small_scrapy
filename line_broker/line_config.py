"""
LINE 配置模組，集中管理 LINE API 相關實例
"""
from linebot import LineBotApi, WebhookHandler
from app.config.settings import settings
from scraper.utils.logger import setup_logger

# 使用自定義的logger設置
logger = setup_logger(__name__)

# 初始化 LINE API 實例
try:
    line_bot_api = LineBotApi(settings.line_channel_token)
    handler = WebhookHandler(settings.line_channel_secret)
    logger.info("LINE API 初始化成功")
except Exception as e:
    logger.error(f"LINE API 初始化失敗: {str(e)}")
    raise 