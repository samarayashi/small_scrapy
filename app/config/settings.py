import os
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv
from scraper.utils.logger import setup_logger

# 設置日誌
logger = setup_logger(__name__)

# 加載環境變量
load_dotenv()

@dataclass
class Settings:
    """應用程式配置"""
    # 環境
    env: str = os.getenv("NODE_ENV", "development")
    
    # 資料庫
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # SQLAlchemy配置
    sql_echo: bool = os.getenv("SQL_ECHO", "false").lower() == "true"
    

    # 天氣 API 配置
    owm_api_key: Optional[str] = os.getenv("OWM_API_KEY")

    # LINE 配置
    line_channel_token: Optional[str] = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret: Optional[str] = os.getenv("LINE_CHANNEL_SECRET")
    def validate(self) -> None:
        """驗證配置"""
        if not self.database_url:
            logger.warning("DATABASE_URL 未設置，某些功能可能無法正常運作")

# 創建配置實例並轉換為字典
settings = Settings()
try:
    settings.validate()
    logger.info(f"使用 {settings.env} 環境配置")
    logger.debug(f"資料庫URL: {settings.database_url}")
except ValueError as e:
    logger.error(f"配置驗證失敗: {str(e)}")
    raise