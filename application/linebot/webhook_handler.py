import logging
from decouple import config

from flask import current_app

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, SendMessage, TextSendMessage
from linebot.exceptions import LineBotApiError

# Initiate this module's logger
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

# Define custom subclass
class CustomLineBotApi(LineBotApi):
    def try_reply_then_push(self, token, target_id, reply):
        try:
            self.reply_message(token, reply)
        except LineBotApiError:
            self.push_message(target_id, reply)
            module_logger.error(
                "Message is sent using push. Suspect that something takes too long to generate a response."
            )

# Initiate webhook handler instance
LINE_CHANNEL_SECRET = config("LINE_CHANNEL_SECRET")
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Initiate linebotapi instance
LINE_BOT_ACCESS_TOKEN = config("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = CustomLineBotApi(LINE_BOT_ACCESS_TOKEN)

# Add function to handle MessageEvent with TextMessage type
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    token = event.reply_token
    received_text = event.message.text
    user_id = event.source.user_id
    group_id = event.source.group_id if event.source.type == "group" else user_id

    reply = current_app.config['MASTERMIND'].query_reply(received_text, user_id, group_id)
    if not reply:
        # If reply is None or empty list (something that signals no-reply condition)
        return

    for index, item in enumerate(reply):
        # This loop looks like it's doing not much (almost nothing).
        # I let it be just in case I modify the modules to be able to return things
        # other than str or SendMessage subclass.

        if isinstance(item, SendMessage):
            continue

        if isinstance(item, str):
            reply[index] = TextSendMessage(item)
            continue

    line_bot_api.try_reply_then_push(token, user_id, reply)
