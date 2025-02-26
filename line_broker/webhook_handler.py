"""
新增Webhook處理模組，負責接收LINE平台事件
"""
from flask import Blueprint, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage
from scraper.utils.logger import setup_logger
from line_broker.broker import NotificationBroker
from line_broker.line_config import line_bot_api, handler
from app.database.connection import db_manager

# 使用自定義的logger設置
logger = setup_logger(__name__)

# 建立藍圖
webhook_blueprint = Blueprint('webhook', __name__)

@webhook_blueprint.route("/webhook", methods=['POST'])
def callback():
    """處理 LINE Webhook 回調"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@webhook_blueprint.route("/health", methods=["GET"])
def test_route():
    """測試路由，確認服務是否正常運行"""
    return "Webhook testing is working!", 200

# 註冊事件處理
@handler.add(FollowEvent)
def handle_follow(event):
    """處理用戶加入好友事件"""
    user_id = event.source.user_id
    logger.info(f"新用戶加入: {user_id}")
    try:
        # 取得資料庫會話
        with db_manager.get_session() as session:
            # 使用broker處理註冊
            broker = NotificationBroker(
                db_session=session,
                line_token=line_bot_api.channel_access_token,
                owm_api_key=None  # 根據需要傳入
            )
            user = broker.handle_user_registration(user_id)
            
            # 發送歡迎訊息
            welcome_msg = f"歡迎 {user.user_name}!\n請使用以下指令操作：\n- 訂閱天氣 [地點]\n- 訂閱新聞 [類別]"
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text=welcome_msg)
            )
    except Exception as e:
        logger.error(f"處理新用戶失敗: {str(e)}")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理用戶文字訊息"""
    # 需要實作指令處理邏輯
    pass

def run(self, host='0.0.0.0', port=5000):
    try:
        self.app.run(host=host, port=port)
    finally:
        self.scheduler.shutdown()  # 確保伺服器關閉時停止排程 