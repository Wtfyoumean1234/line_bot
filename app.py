import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import atexit

load_dotenv()

app=Flask(__name__)

line_bot_api=LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))#幹有夠長三小
handler=WebhookHandler(os.getenv('CHANNEL_SECRET'))

user_ids=set()

@app.route("/webhook", methods=['POST'])
def webhook():
    signature=request.headers['X-Line-Signature']
    body=request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id=event.source.user_id
    user_ids.add(user_id)
    print(f'用戶 ID: {user_id}')
    
    reply_text=f'你說了: {event.message.text}'
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def send_scheduled_message():#公告
    message=TextSendMessage(text='哈哈 屁眼')
    
    for user_id in user_ids:
        try:
            line_bot_api.push_message(user_id, message)
            print(f'訊息已發送給: {user_id}')
        except Exception as e:
            print(f'發送失敗: {e}')

scheduler=BackgroundScheduler()
scheduler.add_job(
    func=send_scheduled_message,
    trigger="cron",
    hour=1,  # UTC時間1:00=台灣時間9:00
    minute=0
)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route("/", methods=['GET'])
def home():
    return 'LINE Bot is running!'

if __name__ == "__main__":
    port=int(os.getenv('PORT',5000))
    app.run(host='0.0.0.0',port=port)
