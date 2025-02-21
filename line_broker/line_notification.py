import requests
import logging
from owm_weather.utils import trans_temp_k2c

logger = logging.getLogger(__name__)

class LineNotification:
    """LINE 通知服務類別，處理訊息發送和格式化"""
    
    LINE_API_URL = "https://api.line.me/v2/bot/message/push"

    def __init__(self, channel_token, user_data):
        """
        初始化 LINE Messaging API 通知工具
        :param channel_token: LINE Channel Access Token
        :param user_data: 使用者資料字典，包含 user_id 和 user 資訊: 如天氣地點、新聞類型
        """
        self._line_token = channel_token
        self.user_data = user_data
        
    def _format_user_data(self):
        return str({
            '使用者': self.user_data.get('user', 'Null'),
            '地點': self.user_data.get('location_name', 'Null'),
        })

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
    
    def _format_news_msg(self, msg):
        pass

    def notify(self, msg_dict):
        """
        發送通知訊息
        :param msg: 要發送的訊息內容（字典格式）
        :return: LINE API 的回應狀態碼與回應數據
        """
        if msg_dict.get('type') == 'user':
            msg_dict['user'] = self._format_user_data()
        elif msg_dict.get('type') == 'weather':
            msg_dict['weather'] = self._format_weather_msg(msg_dict)
        elif msg_dict.get('type') == 'news':
            msg_dict['news'] = self._format_news_msg(msg_dict)
        else:
            raise ValueError('Invalid message type')
        
        
        logger.info('user: %s notify message: %s',
                   self.user_data.get('user', 'NAME_IS_NEEDED'),
                   msg_dict)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._line_token}",
        }
        
        last_response = None
        for msg in msg_dict.values():
            payload = {
                "to": self.user_data['user_id'],
                "messages": [
                    {"type": "text", "text": msg}
                ],
            }
            response = requests.post(self.LINE_API_URL, headers=headers, json=payload)
            last_response = response
        return last_response.status_code, last_response.json()
