import requests
from scraper.utils.logger import setup_logger   

# 使用自定義的logger設置
logger = setup_logger(__name__)

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

    def notify(self, msgs: str | list[str]):
        """
        發送通知訊息
        :param msg_list: 要發送的訊息列表
        :return: LINE API 的回應狀態碼與回應數據
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._line_token}",
        }
        
        last_response = None
        # 如果 msg_list 是字串，轉換成列表
        if isinstance(msgs, str):
            msgs = [msgs]
            
        for msg in msgs:
            payload = {
                "to": self.user_data['user_id'],
                "messages": [
                    {"type": "text", "text": msg}
                ],
            }
            response = requests.post(self.LINE_API_URL, headers=headers, json=payload)
            last_response = response
        return last_response.status_code, last_response.json()
