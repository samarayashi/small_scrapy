import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

class BaseConfig:
    """基礎配置"""
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    ENV: str = os.getenv("NODE_ENV", "development")

class DevelopmentConfig(BaseConfig):
    """開發環境配置"""
    pass

class ProductionConfig(BaseConfig):
    """生產環境配置"""
    pass

def get_config() -> Dict[str, Any]:
    """獲取當前環境的配置"""
    env = os.getenv("NODE_ENV", "development")
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig
    }
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class().__dict__

# 導出當前配置
config = get_config() 