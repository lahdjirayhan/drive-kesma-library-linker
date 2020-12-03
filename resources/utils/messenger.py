class Messenger:
    def __init__(self):
        self.reply_array = []                 # Stores the reply array
        self.join_game = False
        self.unjoin_game = False
        self.end_game = False
    
    def add_reply(self, chat):
        """
        Adds chat to reply_array.
        chat must be a single *SendMessage object, not iterable. This to messenger is as append to list.
        """
        self.reply_array.append(chat)
    
    def add_replies(self, chats):
        """
        Adds chat to reply_array.
        chat must be an iterable of *SendMessage object. This to messenger is as extend to list.
        """
        self.reply_array.extend(chats)