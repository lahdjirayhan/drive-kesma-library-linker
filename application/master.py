from application.attendance import absen_from_line
from application.auth import access_database_from_line
from application.zoom import find_zoom_link_from_line
from application.drive_linker import browse_library_from_line

class Mastermind:
    """
    Temporary docstring:

    Mastermind is an entity that holds business logic, i.e.
    LINE bot gets a chat -> LINE bot 'asks' Mastermind what to do about it ->
    Mastermind processes the chat -> Mastermind tells LINE bot what to say back
    LINE bot replies to user.

    Permissions/capabilities:
    - Drive instance (yes), to obtain e-book links
    - Database access (yes), to do zoomfinding and attendance
    - Reply/bot control (no), only provides replies in form of list of str/dict
    """
    def __init__(self, drive, db):
        self.drive = drive
        self.db = db
        self.identifiers = {
            "!": "attendance",
            "^": "zoomfinding",
            "*": "database access/authorization",
            "ebook": "drive for ebook",
            "bank soal": "drive for bank soal"
        }
    
    def query_reply(self, received_text, user_id, group_id):
        # TODO(Rayhan) make the decision to call function dependent on received_text
        # call either absen_from_line, find_zoom_from_line, access_db_from_line,
        # or what drivelinker provides; with their key identifier removed

        # Huge note to self: please read each function before writing here.
        # Don't use top-of-head memory. Be sensible and careful.
        key, rest_of_the_chat = self._split_to_keyword_and_arguments(received_text)
        if key == "!":
            return absen_from_line(rest_of_the_chat, user_id)
        if key == "*":
            return access_database_from_line(rest_of_the_chat, self.db, user_id)
        if key == "^":
            return find_zoom_link_from_line(rest_of_the_chat, user_id)
        if key in ['ebook', 'soal']:
            if rest_of_the_chat == '':
                return browse_library_from_line(self.drive, key, None, user_id)
            return browse_library_from_line(self.drive, key, rest_of_the_chat, user_id)

        return []
        
        
    def _split_to_keyword_and_arguments(self, text):
        """Splits to key and argument

        Priorities:
        - Check if first character is an identifier. If yes, return that identifier as key and the rest of string as argument
        - Check if first word (whitespace as separator) is an identifier. If yes, return key and argument via str.partition
        """
        if text[0] in self.identifiers:
            key, argument = text[0], text[1:].strip()
        elif text.partition(" ")[0] in self.identifiers:
            key, _, argument = text.partition(" ")
        else:
            key, argument = None, None
        return key, argument
        
    
    # def send_reply(self, token, reply_array):
    #     """
    #     Send reply_array as the reply to user using token.
    #     reply_array should be iterables of *SendMessage
    #     """
    #     if reply_array != []:
    #         self.bot.reply_message(
    #             token,
    #             reply_array
    #         )
    
    # def send_push(self, target_id, reply_array):
    #     """
    #     Send reply_array as a push message.
    #     reply_array should be iterables of *SendMessage
    #     """
    #     # This is originally implemented for its-absen as remedy for invalid reply token.
    #     if reply_array != []:
    #         self.bot.push_message(
    #             target_id,
    #             reply_array
    #         )
    
    # def try_send_reply_then_send_push(self, token, target_id, reply_array):
    #     """
    #     Try sending reply_array as a reply. If it fails due to timeout,
    #     and thus invalid token, send reply_array as push message instead.
    #     """
    #     # This is implemented when its-zoom is added, not to violate Don't Repeat Yourself principle.
    #     try:
    #         self.send_reply(
    #             token,
    #             reply_array
    #         )
    #     except LineBotApiError as error:
    #         if error.error.message == "Invalid reply token":
    #             self.send_push(
    #                 target_id,
    #                 reply_array
    #             )
    
    # def add_player_to_game(self, user_id, group_id):
    #     if user_id not in self.memberships:
    #         self.memberships[user_id] = group_id
    
    # def remove_player_from_game(self, user_id):
    #     if user_id in self.memberships:
    #         del self.memberships[user_id]
    
    # def add_game(self, group_id, game):
    #     if group_id not in self.games:
    #         if hasattr(game, "set_drive"):
    #             # Set pydrive.GoogleDrive object, see DriveLinker.set_drive
    #             game.set_drive(self.drive)
    #         self.games[group_id] = game
    
    # def remove_game(self, group_id):
    #     if group_id in self.games:
    #         self.memberships = {k: v for k, v in self.memberships.items() if v != group_id}
    #         del self.games[group_id]
    
    # def leave_group(self, group_id):
    #     self.remove_game(group_id)
    #     self.bot.leave_group(group_id)
    
    # # Main engine(s) of Mastermind. Reads the received text, then decide
    # # what to do or to reply.
    # def query_reply(self, token, received_text, user_id, group_id):
    #     try:
    #         display_name = self.bot.get_profile(user_id).display_name
    #     except (LineBotApiError, AttributeError) as error:
    #         display_name = "UNKNOWN_NAME_PLEASE_ADD_AS_FRIEND"
        
    #     if received_text.startswith(self.keyword_add_game):
    #         # Filter if already in some game
    #         if user_id in self.memberships:
    #             return
            
    #         # Note to self: implement system where user can choose what to play.
    #         try:
    #             preferred_game = self.gamelist[received_text.split(" ", 1)[1]]
    #         except (KeyError, IndexError) as error:
    #             self.send_reply(
    #                 token,
    #                 TextSendMessage(
    #                     text = "Please specify a valid game specifier: cf for Connect Four, hm for Hangman, tt for Tictactoe"
    #                 )
    #             )
    #         else:
    #             try:
    #                 self.add_game(group_id, preferred_game())
    #                 self.add_player_to_game(user_id, group_id)
                    
    #                 received_messenger = self.games[self.memberships[user_id]].start_game()
    #                 self.send_reply(
    #                     token,
    #                     received_messenger.reply_array
    #                 )
    #             except KeyError as error:
    #                 return
        
    #     elif received_text == self.keyword_remove_game:
    #         try:
    #             # To prevent a person somehow sneaking a /gameoff. Test for bugs.
    #             if self.memberships[user_id] != group_id:
    #                 return
                
    #             received_messenger = self.games[self.memberships[user_id]].end_game()
    #             self.send_reply(
    #                 token,
    #                 received_messenger.reply_array
    #             )
    #             self.remove_game(group_id)
    #         except KeyError as error:
    #             return
    #     elif received_text.startswith("!"):
    #         # Assure the absensi will only work in private chat with OA.
    #         if user_id != group_id:
    #             return
    #         # Send unparsed text but without the ! sign
    #         received_messenger = absen_from_line(received_text[1:], user_id=user_id)
            
    #         # If reply_message results in an error, do push_message
    #         self.try_send_reply_then_send_push(token, user_id, received_messenger.reply_array)
        
    #     elif received_text.startswith("*"):
    #         # Assure the database access will only work in private chat with OA.
    #         if user_id != group_id:
    #             return
    #         # Send unparsed text but without the * sign
    #         received_messenger = access_database_from_line(received_text[1:], db=self.db, user_id=user_id)
    #         self.send_reply(
    #             token,
    #             received_messenger.reply_array
    #         )
        
    #     elif received_text.startswith("^"):
    #         # Assure the zoom finding access will only work in private chat with OA.
    #         if user_id != group_id:
    #             return
    #         # Send unparsed text but without the ^ sign
    #         received_messenger = find_zoom_link_from_line(received_text[1:], user_id=user_id)
            
    #         # If reply_message results in an error, do push_message
    #         self.try_send_reply_then_send_push(token, user_id, received_messenger.reply_array)
            
    #     else:
    #         try:
    #             received_messenger = self.games[self.memberships[user_id]].parse_and_reply(received_text, user_id, display_name, group_id)
    #             self.send_reply(
    #                 token,
    #                 received_messenger.reply_array
    #             )
    #             if received_messenger.end_game:
    #                 self.remove_game(group_id)
    #             if received_messenger.join_game:
    #                 self.add_player_to_game(user_id, group_id)
    #         except (KeyError, AttributeError) as error:
    #             return
