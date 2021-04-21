from flask import Blueprint, current_app, request, abort
from linebot.exceptions import InvalidSignatureError

from application.linebot.webhook_handler import handler

line_callback = Blueprint('callback', __name__)

@line_callback.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    current_app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'
