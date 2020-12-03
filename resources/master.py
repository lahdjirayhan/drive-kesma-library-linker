from .games import ConnectFour
from .games import Hangman
from .games import Tictactoe
from .games import DriveLinker

from .absen import absen
from .absen import matkul_abbreviations

from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

class MasterDriveHandler:
    """
    Mastermind-type class to handle intermediary between LINE Messaging API
    and group-level game module.
    
    BY DEFINITION, MASTERMIND IS TIED TO LINEBOTAPI.
    
    Mastermind REPLIES the user, using reply_array that is PROVIDED
    by the respective game instances. The chat types (Text, Flex, etc)
    is PROVIDED by the respective game instances.
    
    Mastermind CONTROLS the user association with a group and/or a game,
    and IS RESPONSIBLE for keeping track of said association. The game
    instance does not have control over add_game and remove_game; but they
    DO HAVE control over join and unjoin to make Mastermind's job easier.
    """
    def __init__(self, line_bot_api, drive):
        self.bot = line_bot_api
        self.drive = drive
        self.games = {}
        self.memberships = {}
        
        self.gamelist = {"cf": ConnectFour, "hm": Hangman, "tt": Tictactoe, "dr": DriveLinker}
        
        self.keyword_show_game_list = "/list"    # "Show me games that I can play."
        self.keyword_add_game = "/gameon"        # "Give this chat a game."
        self.keyword_remove_game = "/gameoff"    # "Remove game from this chat."
        self.keyword_leave = "/goaway"           # "Leave from this chat/group. (?)"
    
    def send_reply(self, token, reply_array):
        """
        Send reply_array as the reply to user using token.
        reply_array should be iterables of *SendMessage
        """
        if reply_array != []:
            self.bot.reply_message(
                token,
                reply_array
            )
    
    def send_push(self, target_id, reply_array):
        """
        Send reply_array as a push message.
        reply_array should be iterables of *SendMessage
        """
        # This is originally implemented for its-absen as remedy for invalid reply token.
        if reply_array != []:
            self.bot.push_message(
                target_id,
                reply_array
            ) 
    
    def add_player_to_game(self, user_id, group_id):
        if user_id not in self.memberships:
            self.memberships[user_id] = group_id
    
    def remove_player_from_game(self, user_id):
        if user_id in self.memberships:
            del self.memberships[user_id]
    
    def add_game(self, group_id, game):
        if group_id not in self.games:
            if hasattr(game, "set_drive"):
                # Set pydrive.GoogleDrive object, see DriveLinker.set_drive
                game.set_drive(self.drive)
            self.games[group_id] = game
    
    def remove_game(self, group_id):
        if group_id in self.games:
            self.memberships = {k: v for k, v in self.memberships.items() if v != group_id}
            del self.games[group_id]
    
    def leave_group(self, group_id):
        self.remove_game(group_id)
        self.bot.leave_group(group_id)
    
    # Main engine(s) of Mastermind. Reads the received text, then decide
    # what to do or to reply.
    def query_reply(self, token, received_text, user_id, group_id):
        try:
            display_name = self.bot.get_profile(user_id).display_name
        except (LineBotApiError, AttributeError) as error:
            display_name = "UNKNOWN_NAME_PLEASE_ADD_AS_FRIEND"
        
        if received_text.startswith(self.keyword_add_game):
            # Filter if already in some game
            if user_id in self.memberships:
                return
            
            # Note to self: implement system where user can choose what to play.
            try:
                preferred_game = self.gamelist[received_text.split(" ", 1)[1]]
            except (KeyError, IndexError) as error:
                self.send_reply(
                    token,
                    TextSendMessage(
                        text = "Please specify a valid game specifier: cf for Connect Four, hm for Hangman, tt for Tictactoe"
                    )
                )
            else:
                try:
                    self.add_game(group_id, preferred_game())
                    self.add_player_to_game(user_id, group_id)
                    
                    received_messenger = self.games[self.memberships[user_id]].start_game()
                    self.send_reply(
                        token,
                        received_messenger.reply_array
                    )
                except KeyError as error:
                    return
        
        elif received_text == self.keyword_remove_game:
            try:
                # To prevent a person somehow sneaking a /gameoff. Test for bugs.
                if self.memberships[user_id] != group_id:
                    return
                
                received_messenger = self.games[self.memberships[user_id]].end_game()
                self.send_reply(
                    token,
                    received_messenger.reply_array
                )
                self.remove_game(group_id)
            except KeyError as error:
                return
        elif received_text.startswith("/"):
            # This block is put here as lazy, 'temporary', solution to catch names or abbreviations of a course name.
            splitlist = received_text.rsplit(" ", 1) # Split from the right
            try:
                matkul = splitlist[0][1:]
                kode_absen = splitlist[1]
            except IndexError:
                self.send_reply(
                    token,
                    TextSendMessage("Either missing matkul name or kode absen.")
                )
                return
            
            try:
                matkul_proper_name = matkul_abbreviations[matkul]
            except KeyError as error:
                self.send_reply(
                    token,
                    TextSendMessage("Matkul name is wrong or not recognized!")
                )
                return
            
            received_messenger = absen(matkul_proper_name, kode_absen)
            # If reply_message results in an error, do push_message
            try:
                self.send_reply(
                    token,
                    received_messenger.reply_array
                )
            except LineBotApiError as error:
                if error.error.message == "Invalid reply token":
                    self.send_push(
                        user_id,
                        received_messenger.reply_array
                    )
                    return
            
        else:
            try:
                received_messenger = self.games[self.memberships[user_id]].parse_and_reply(received_text, user_id, display_name, group_id)
                self.send_reply(
                    token,
                    received_messenger.reply_array
                )
                if received_messenger.end_game:
                    self.remove_game(group_id)
                if received_messenger.join_game:
                    self.add_player_to_game(user_id, group_id)
            except (KeyError, AttributeError) as error:
                return
