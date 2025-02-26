"""
line_broker/broker.py

負責處理訊息發送的邏輯：
1. 讀取資料庫中的訂閱資訊
2. 根據訂閱類型（天氣/新聞）獲取相應資料
3. 格式化訊息
4. 發送 LINE 通知
"""

from scraper.utils.logger import setup_logger
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import User, SubWeather, SubNews
from app.models.news import NewsArticle, NewsCategory
from owm_weather.Weather_station import WeatherStation
from .line_notification import LineNotification

from owm_weather.utils import trans_temp_k2c

# 使用自定義的logger設置
logger = setup_logger(__name__)

class NotificationBroker:
    """通知代理類，處理訂閱通知的發送邏輯"""
    
    def __init__(
        self,
        db_session: Session,
        line_token: str,
        owm_api_key: Optional[str] = None
    ):
        """
        初始化通知代理
        
        Args:
            db_session: SQLAlchemy session，用於資料庫操作
            line_token: LINE Channel Access Token
            owm_api_key: OpenWeatherMap API Key（可選，僅在需要發送天氣通知時必須）
        """
        self.session = db_session
        self.line_token = line_token
        self.weather_station = (
            WeatherStation(owm_api_key=owm_api_key) if owm_api_key else None
        )
    
    def _get_weather_data(self, longitude: float, latitude: float) -> Dict:
        """
        獲取指定位置的天氣資料
        
        Args:
            longitude: 經度
            latitude: 緯度
            
        Returns:
            天氣資料字典
        """
        if not self.weather_station:
            raise ValueError("Weather station not initialized. Missing OWM API key.")
        return self.weather_station._get_data_by_coord(longitude, latitude)
    
    def _get_latest_news(
        self, 
        category_key: str, 
        limit: int = 5
    ) -> List[NewsArticle]:
        """
        獲取指定分類的最新新聞
        
        Args:
            category_key: 新聞分類代碼
            limit: 獲取的新聞數量（預設5則）
            
        Returns:
            新聞文章列表
        """
        return (
            self.session.query(NewsArticle)
            .filter(NewsArticle.news_category_key == category_key)
            .order_by(desc(NewsArticle.publish_time))
            .limit(limit)
            .all()
        )
        
    def _format_weather_msg(self, msg):
        """
        格式化天氣訊息
        :param msg: 天氣訊息字典
        :return: 格式化後的字串
        """
        return str({
            '溫度': trans_temp_k2c(msg.get('temperature', {}).get('temp', 'Null')),
            '濕度': msg.get('humidity', 'Null'),
            '天氣狀態': msg.get('status', 'Null'),
            '詳細天氣狀態': msg.get('detailed_status', 'Null'),
            '風速': msg.get('wind', {}).get('speed', 'Null')
        })
        
    def _format_news_message(
        self, 
        category_name: str, 
        articles: List[NewsArticle]
    ) -> str:
        """
        格式化新聞訊息
        
        Args:
            category_name: 新聞分類名稱
            articles: 新聞文章列表
            
        Returns:
            格式化後的新聞訊息
        """
        if not articles:
            return f"【{category_name}】目前沒有新聞"
        
        lines = [f"【{category_name} 新聞】"]
        for idx, article in enumerate(articles, start=1):
            pub_time = article.publish_time.strftime('%Y-%m-%d %H:%M')
            lines.append(f"{idx}. {article.title}")
            lines.append(f"   發布時間: {pub_time}")
            lines.append(f"   連結: {article.url}\n")
        
        return "\n".join(lines)
    
    def handle_user_registration(self, user_id: str) -> User:
        """處理新用戶註冊並返回用戶物件"""
        try:
            user = self.session.query(User).filter_by(line_user_id=user_id).first()
            if not user:
                user = User(line_user_id=user_id)
                self.session.add(user)
                self.session.commit()
                logger.info(f"新用戶註冊成功: {user_id}")
            return user
        except Exception as e:
            self.session.rollback()
            logger.error(f"用戶註冊失敗: {str(e)}")
            raise
    
    def send_weather_notifications(self) -> None:
        """發送天氣通知給所有訂閱者"""
        logger.info("開始發送天氣通知...")
        
        # 獲取所有天氣訂閱資訊
        weather_subs = (
            self.session.query(SubWeather)
            .join(User)
            .filter(User.is_registered == True)
            .all()
        )
        
        if not weather_subs:
            logger.info("沒有天氣訂閱資料")
            return
        
        for sub in weather_subs:
            try:
                # 獲取天氣資料
                weather_data = self._get_weather_data(
                    longitude=sub.longitude,
                    latitude=sub.latitude
                )
                
                # 準備使用者資料
                user_data = {
                    "user": sub.user.user_name,
                    "user_id": sub.user.line_user_id,
                    "location_name": sub.location_name
                }
                
                # 發送通知
                notifier = LineNotification(self.line_token, user_data)
                msg = self._format_weather_msg(weather_data)
                status, response = notifier.notify(msg)
                logger.info(
                    f"天氣通知發送成功 - 使用者: {sub.user.user_name}, "
                    f"地點: {sub.location_name}, status: {status}"
                )
                
            except Exception as e:
                logger.error(
                    f"天氣通知發送失敗 - 使用者: {sub.user.user_name}, "
                    f"地點: {sub.location_name}, error: {str(e)}"
                )
    
    def send_news_notifications(self) -> None:
        """發送新聞通知給所有訂閱者"""
        logger.info("開始發送新聞通知...")
        
        # 獲取所有新聞訂閱資訊
        news_subs = (
            self.session.query(SubNews)
            .join(User)
            .filter(User.is_registered == True)
            .all()
        )
        
        if not news_subs:
            logger.info("沒有新聞訂閱資料")
            return
        
        for sub in news_subs:
            try:
                # 獲取最新新聞
                articles = self._get_latest_news(sub.news_category_key)
                
                # 格式化訊息
                news_message = self._format_news_message(
                    sub.news_category.category_name,
                    articles
                )
                
                # 準備使用者資料
                user_data = {
                    "user": sub.user.user_name,
                    "user_id": sub.user.line_user_id
                }
                
                # 發送通知
                notifier = LineNotification(self.line_token, user_data)
                status, response = notifier.notify(news_message)
                
                logger.info(
                    f"新聞通知發送成功 - 使用者: {sub.user.user_name}, "
                    f"分類: {sub.news_category.category_name}, status: {status}"
                )
                
            except Exception as e:
                logger.error(
                    f"新聞通知發送失敗 - 使用者: {sub.user.user_name}, "
                    f"分類: {sub.news_category.category_name}, error: {str(e)}"
                )
