#!/usr/bin/env python3
"""
發送訂閱通知的主程式
使用方式：
    python send_notifications.py [--weather-only|--news-only]
"""

import argparse
from scraper.utils.logger import setup_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from .broker import NotificationBroker

# 設置日誌
logger = setup_logger(__name__)

def parse_args():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(description='發送訂閱通知')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--weather-only', action='store_true', help='僅發送天氣通知')
    group.add_argument('--news-only', action='store_true', help='僅發送新聞通知')
    return parser.parse_args()

def main():
    """主程式"""
    args = parse_args()
    
    # 驗證必要的設定
    if not settings.database_url:
        raise ValueError("未設置資料庫連接字串 (DATABASE_URL)")
    if not settings.line_channel_token:
        raise ValueError("未設置 LINE Channel Access Token")
    
    # 建立資料庫連線
    engine = create_engine(settings.database_url, echo=settings.sql_echo)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 初始化通知代理
        broker = NotificationBroker(
            db_session=session,
            line_token=settings.line_channel_token,
            owm_api_key=settings.owm_api_key
        )
        
        # 根據參數決定發送哪種通知
        if args.weather_only:
            if not settings.owm_api_key:
                raise ValueError("未設置 OpenWeatherMap API Key")
            broker.send_weather_notifications()
        elif args.news_only:
            broker.send_news_notifications()
        else:
            # 預設發送所有類型的通知
            if settings.owm_api_key:
                broker.send_weather_notifications()
            broker.send_news_notifications()
            
    except Exception as e:
        logger.error(f"發送通知時發生錯誤: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    main() 