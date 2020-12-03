# Imports here

from ..utils import Messenger

from linebot.models import TextSendMessage, FlexSendMessage

# Non-optional methods required by Master
class AppName:
    def __init__(self):
        pass
    
    def start_game(self):
        pass
    
    def end_game(self):
        pass
    
    def parse_and_reply(self):
        pass