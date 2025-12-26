import os
import atexit
import random
from datetime import datetime, timedelta

from flask import Flask, request, abort
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
)

load_dotenv()

app = Flask(__name__)

# ✅ 建議新版環境變數命名（你也可以維持原本的名字）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise RuntimeError("Missing CHANNEL_ACCESS_TOKEN/CHANNEL_SECRET (or LINE_CHANNEL_ACCESS_TOKEN/LINE_CHANNEL_SECRET)")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

user_ids = set()
interval= dict()
'''
format:
gay:{
    hour:6,
    minute:9
    notmsg:"去打手槍"
    worktime:1
    endtime:1
    anno:False
}
'''

talk3small=["你腦霧吧",
            "喔咿咿阿依喔咿咿咿阿依",
            "ㄟㄟ快看那裏有個傻逼",
            "你知道把你女朋友形容成一把劍叫做看不劍",
            "吃~~~雞~~~~雞~~~喔~~~~喔~~~喔~~~~~~~~~",
            "麵框框超頂去吃它",
            "你知道把費米子轉一圈他的波函數會轉180度嗎?",
            "如果你餓了不吃東西，可以吃我屌",
            "又!又舔!又舔嘴唇!!!",
            "冷知識：什麼東西是綠色的掉下去會砸死人?\n台球桌",
            "如果你現在肚子餓的話，可以去廁所看看，你就會沒食慾摟~",
            "小明對芒果過敏，那他不能吃什麼?\n他不能吃芒果\n你以為我要說台球桌是不是:))))))",
            "你知道你為什麼要讀書嗎?\n我也不知道，反正你在廢下去我就打斷你的腿",
            "不要再打了，要打去練舞室打",
            "聽話，讓我看看!!!",
            "這件事是我們兩個之間的秘密，你最好不要給我告訴任何人，如果你要說出去，就給我小心一點",
            "我知道你學校在哪，也知道你讀哪一班，你最好給我好好記住，懂嗎?",
            "不要!!!杰哥不要啦，杰哥不要.....杰哥不要，杰歌",
            "前列腺高潮來臨時，腰部以下特別是陰腹部位幾乎完全麻痺",
            "這種收縮運動大概只有幾秒鐘，收縮過後就是強烈的高潮到來",
            "整個身體好像一朵雲，輕飄飄的浮在空中，完全虛脫失去重力",
            "我電腦放客廳，家人聽得道你在說什麼",
            "爸爸媽媽，你兒子在了解前列腺的事情啦",
            "彈幕一個觀眾說：台灣人文明的讓我受不了"]

tuto="print <msg,gap,sleeptime>\n" \
     "輸出對應資訊" \
     "/stop gap <天數> <小時數> <分鐘數>\n" \
     "暫時停止bot煩，時間代表停止的間隔，過後便會馬上開始\n" \
     "/stop set <年> <月> <天數> <小時> <分鐘>\n" \
     "暫時停止bot煩，時間代表停用至什麼時候，過後便馬上開始\n" \
     "/stop forever\n" \
     "永久停止\n" \
     "/setgap <小時> <分鐘>\n" \
     "設定提醒之間的gap\n" \
     "/setmsg <提示詞>\n" \
     "設定提示詞\n" \
     "/sleeptime <開始睡覺時間> <停止睡覺時間>\n" \
     "設定睡覺時間\n" \
     "/startnow\n" \
     "提示計時現在結束" \
     ""

@app.route("/webhook", methods=["POST"])
def webhook():
    signature=request.headers.get("X-Line-Signature", "")
    body=request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

def notifyreset(sche,usr_id):
    runtime=datetime.now()+timedelta(hours=interval[usr_id]['hour'],minutes=interval[usr_id]['minute'])
    curhr=datetime.now().hour
    worktime=interval[usr_id]['worktime']
    endtime=interval[usr_id]['endtime']
    if (worktime>=endtime and (curhr>=worktime or curhr<=endtime)) or (worktime<endtime and (curhr>=worktime and curhr<=endtime)):return
    noti_id=f"{usr_id},notify"
    anno_id=f"{usr_id},annoy"
    interval[usr_id]['anno']=True
    print("執行noti")
    setsche(runtime,noti_id,notifyreset,[sche,usr_id])
    if not is_job_scheduled(sche,anno_id):setsche(datetime.now(),anno_id,frequent_message,[sche,usr_id,0])
    sche.print_jobs()

def wakeup(sche,usr_id):
    notifyreset(sche,usr_id)

def frequent_message(sche,usr_id,count):
    if not interval[usr_id]['anno'] or count>10:return
    count+=1
    with ApiClient(configuration) as api_client:
        messaging_api=MessagingApi(api_client)
        messaging_api.push_message(
            PushMessageRequest(
                to=usr_id,
                messages=[TextMessage(text=interval[usr_id]['notmsg'])],
            )
        )
    runtime=datetime.now()+timedelta(seconds=1,milliseconds=500)
    anno_id=f"{usr_id},annoy"
    setsche(runtime,anno_id,frequent_message,[sche,usr_id,count])

def is_job_scheduled(sche, job_id:str)->bool:
    job=sche.get_job(job_id)
    return job is not None

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    usr_id=event.source.user_id
    sleep_id=f"{usr_id},sleep"
    noti_id=f"{usr_id},notify"
    anno_id=f"{usr_id},annoy"
    if usr_id not in user_ids:
        user_ids.add(usr_id)
        interval[usr_id]={
            'hour':0,
            'minute':1,
            'notmsg':"去讀書拉",
            'worktime':23,
            'endtime':8,
            'anno':False
        }
        inittime=datetime.now()
        setsche(inittime,noti_id,notifyreset,[sche,usr_id])
    interval[usr_id]['anno']=False
    intext=event.message.text
    print(f"用戶 ID: {usr_id} 輸入 {intext}")
    curhr=datetime.now().hour
    worktime=interval[usr_id]['worktime']
    endtime=interval[usr_id]['endtime']
    if (worktime>=endtime and (curhr>=worktime or curhr<=endtime)) or (worktime<endtime and (curhr>=worktime and curhr<=endtime)):
        reply_text="去睡覺"
        intext=f"{usr_id} is the asshole who doesnt go to sleep at {datetime.now().hour}:{datetime.now().minute}"
    else:
        reply_text="指令還沒設好;D"
        cs=intext.split()
        if cs[0][0]=='/':
            match cs[0]:
                case "/help":
                    reply_text=tuto
                case "/print":
                    try:
                        if cs[1]=="msg":
                            reply_text=interval[usr_id]['notmsg']
                        elif cs[1]=="gap":
                            reply_text=f"{interval[usr_id]['hour']}小時{interval[usr_id]['minute']}分鐘"
                        elif cs[1]=="sleeptime":
                            if worktime>=endtime:
                                reply_text=f"睡覺時間：{worktime}~{endtime}"
                        else:
                            raise SyntaxError
                    except:
                        reply_text="參數錯誤，格式應為/print <msg,gap,sleeptime>"
                case "/stop":
                    if is_job_scheduled(sche,sleep_id):
                        reply_text="別吵林北，林北在睡覺"
                    elif len(cs)>1 and cs[1]=="gap":
                        try:
                            runtime=datetime.now()+timedelta(days=int(cs[2]),hours=int(cs[3]),minutes=int(cs[4]))
                            if is_job_scheduled(sche,noti_id):sche.remove_job(noti_id)
                            if is_job_scheduled(sche,anno_id):sche.remove_job(anno_id)
                            setsche(runtime,sleep_id,wakeup,[sche,usr_id])
                            reply_text="設定成功\n請你務必要知道你自己在做什麼，為你自己的選擇負責任"
                        except:
                            reply_text="參數錯誤，格式應為/stop gap <天數> <小時數> <分鐘數>"
                    elif len(cs)>1 and cs[1]=="set":
                        try:
                            runtime=datetime(year=int(cs[2]),month=int(cs[3]),day=int(cs[4]),hour=int(cs[5]),minute=int(cs[6]))
                            if runtime<datetime.now():
                                reply_text="不可設過去的時間"
                            else:
                                setsche(runtime,sleep_id,wakeup,[sche,usr_id])
                                reply_text="設定成功\n請你務必要知道你自己在做什麼，為你自己的選擇負責任"
                        except:
                            reply_text="參數錯誤，格式應為/stop set <年> <月> <天數> <小時> <分鐘>"
                    elif len(cs)>1 and cs[1]=="forever":
                        reply_text="你傻逼吧你真以為有這種功能喔"
                    else:
                        reply_text="參數錯誤，格式應為/stop <gap,set>"
                case "/setgap":
                    try:
                        interval[usr_id]['hour']=int(cs[1])
                        interval[usr_id]['minute']=int(cs[2])
                        if is_job_scheduled(sche,noti_id):sche.remove_job(noti_id)
                        setsche(datetime.now(),noti_id,notifyreset,[sche,usr_id])
                        reply_text="設定成功，計時器從現在開始重製"
                    except:
                        reply_text="參數錯誤，格式應為/setgap <小時> <分鐘>"
                case "/setmsg":
                    try:
                        interval[usr_id]['notmsg']=cs[1]
                        for i in range(2,len(cs)):
                            interval[usr_id]['notmsg']+=" "+cs[i]
                        reply_text="設定成功"
                    except:
                        reply_text="參數錯誤，格式應為/setmsg <提示詞>"
                case "/sleeptime":
                    try:
                        interval[usr_id]['worktime']=int(cs[1])
                        interval[usr_id]['endtime']=int(cs[2])
                        reply_text="設定成功"
                    except:
                        reply_text="參數錯誤，格式應為/sleeptime <開始睡覺時間> <停止睡覺時間>"
                case "/startnow":
                    try:
                        if is_job_scheduled(sche,sleep_id):sche.remove_job(sleep_id)
                        if is_job_scheduled(sche,noti_id):sche.remove_job(noti_id)
                        notifyreset(sche,usr_id)
                        reply_text="設定成功"
                    except:
                        reply_text="執行錯誤，可能屁眼張的不夠開哈哈"
                case "/fuckyourmom":
                    pass
                case _ :
                    reply_text="非法指令，想知道可用指令請打/help"
        else:
            if is_job_scheduled(sche,anno_id):sche.remove_job(anno_id)
            reply_text=talk3small[random.randint(0,len(talk3small)-1)]

    with ApiClient(configuration) as api_client:
        messaging_api=MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )

def setsche(date,job_id,func,args):
    sche.add_job(
        func=func,
        trigger="date",
        id=job_id,
        run_date=date,
        args=args
    )
    #sche.resume_job(job_id)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    sche=BackgroundScheduler(timezone="Asia/Taipei",
                            job_defaults={
                            'coalesce': True,
                            'misfire_grace_time':60
                            })
    sche.start()
    atexit.register(lambda: sche.shutdown())
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
