# Flask related imports
import os
from decouple import config
from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Initiate Flask app instance
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import and initiate database
from resources.models import db
db.init_app(app)
migrate = Migrate(app, db)

# Non-Flask related imports
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from resources.master import MasterDriveHandler
from resources.utils import initialize_credential_decryption

# Perform decryption on credential files
initialize_credential_decryption()

# Authorize Google Drive and initiate drive instance
gauth = GoogleAuth()
GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
gauth.LoadCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

# Initiate linebotapi instance
LINE_BOT_ACCESS_TOKEN = config("LINE_CHANNEL_ACCESS_TOKEN", default=os.environ.get('LINE_ACCESS_TOKEN'))
line_bot_api = LineBotApi(LINE_BOT_ACCESS_TOKEN)

# Initiate webhook handler instance
LINE_CHANNEL_SECRET = config("LINE_CHANNEL_SECRET", default = os.environ.get('LINE_CHANNEL_SECRET'))
handler = WebhookHandler(LINE_CHANNEL_SECRET)


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

# Initiate mastermind instance
master = MasterDriveHandler(line_bot_api, drive, db)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # Required to tell Python that the referred variable is in global scope,
    # not creating and using locally-declared variables.
    global master
    
    token = event.reply_token
    received_text = event.message.text
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else user_id
    
    master.query_reply(token, received_text, user_id, group_id)


# Main engine, liftoff!
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)