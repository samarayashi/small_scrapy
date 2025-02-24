"""
新增Webhook處理模組，負責接收LINE平台事件
"""
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage
import logging
from line_broker.broker import NotificationBroker

logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self, channel_secret, channel_token, db_session):
        self.db_session = db_session
        self.line_bot_api = LineBotApi(channel_token)
        self.handler = WebhookHandler(channel_secret)
        self.app = Flask(__name__)

        # 註冊路由處理
        @self.app.route("/webhook", methods=['POST'])
        def callback():
            signature = request.headers['X-Line-Signature']
            body = request.get_data(as_text=True)
            
            try:
                self.handler.handle(body, signature)
            except InvalidSignatureError:
                abort(400)
            return 'OK'

        # 新增測試路由，方便確認公開 URL 是否可正確回應
        @self.app.route("/test", methods=["GET"])
        def test_route():
            return "Webhook testing is working!", 200

        # 註冊事件處理
        @self.handler.add(FollowEvent)
        def handle_follow(event):
            """處理用戶加入好友事件"""
            user_id = event.source.user_id
            logger.info(f"新用戶加入: {user_id}")
            try:
                # 使用broker處理註冊
                broker = NotificationBroker(
                    db_session=self.db_session,
                    line_token=channel_token,
                    owm_api_key=None  # 根據需要傳入
                )
                user = broker.handle_user_registration(user_id)
                
                # 發送歡迎訊息
                welcome_msg = f"歡迎 {user.user_name}!\n請使用以下指令操作：\n- 訂閱天氣 [地點]\n- 訂閱新聞 [類別]"
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextMessage(text=welcome_msg)
                )
            except Exception as e:
                logger.error(f"處理新用戶失敗: {str(e)}")

        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_message(event):
            """處理用戶文字訊息"""
            # 需要實作指令處理邏輯

    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port) 