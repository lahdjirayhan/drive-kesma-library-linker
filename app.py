# Standard imports
import os
from decouple import config
from flask import Flask, request, abort
from waitress import serve
import time

# LINEBOT imports
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Multiprocessing imports
from multiprocessing.managers import BaseManager

# Custom imports
from resources import MasterDriveHandler
from resources.utils import make_drive_instance
    
# The following lines are mostly not self-written
# Initiate Flask app instance
app = Flask(__name__)
# Initiate linebotapi instance
line_bot_api = LineBotApi(
    config("LINE_CHANNEL_ACCESS_TOKEN",
           default=os.environ.get('LINE_ACCESS_TOKEN'))
)
# Initiate handler instance
handler = WebhookHandler(
    config("LINE_CHANNEL_SECRET",
           default=os.environ.get('LINE_CHANNEL_SECRET'))
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Create Drive instance
drive = make_drive_instance()

# Initiate mastermind instance
manager = BaseManager(('', 37844), config("MANAGER_PASSWORD", default = "password").encode())
manager.register('get_mastermind')

def get_master():
    return manager.get_mastermind()



@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):    
    token = event.reply_token
    received_text = event.message.text
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else user_id
    
    get_master().query_reply(token, received_text, user_id, group_id)

# Main engine, liftoff!
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    serve(app, host = "0.0.0.0", port=port)
    time.sleep(60)
    manager.connect()
    print("Manager connected successfully.")
    get_master().embed_line_bot_api(line_bot_api)
    get_master().embed_drive(drive)