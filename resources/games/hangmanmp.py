import numpy as np
import os

from ..utils import Messenger

from linebot.models import TextSendMessage

this_dir, this_filename = os.path.split(__file__)

with open(os.path.join(this_dir, "easy.txt")) as filestream_easy:
    easy = filestream_easy.readlines()

with open(os.path.join(this_dir, "medium.txt")) as filestream_medium:
    medium = filestream_medium.readlines()

with open(os.path.join(this_dir, "hard.txt")) as filestream_hard:
    hard = filestream_hard.readlines()

class HangmanActiveStringMultiplayer:
    def __init__(self):
        self.active_difficulty = None
        self.active_word = ""
        self.active_word_proposer = ""
        self.letter_states = {}
        self.show_string = ""
        self.attempted_letters = ""
        self.waiting_list = []
        self.word_proposer = []
    
    def get_show_string(self):
        """
        Returns show_string, to not directly access self.show_string
        """
        return self.show_string
    
    def update_show_string(self):
        """
        Update the show_string. Not return anything.
        """
        self.show_string = ""
        char_index = 0
        for char in self.active_word:
            if self.letter_states.get(char, True):
                # This way, punctuation and other nonalphabet character is 
                # always shown.
                self.show_string += char
            else:
                self.show_string += "_"
            self.show_string += " "          # Add space after each characters. Will improve readability.
        
    def initiate_letter_states(self):
        """
        For setting the letter states into all-false (no guessed
        letters) after a new word is given.
        """
        unique_letters = self.active_word.upper()
        unique_letters = list(set(list(unique_letters)))
        unique_letters = list(''.join(filter(str.isalpha, ''.join(unique_letters))))
        self.letter_states = {k: False for k in unique_letters}
        self.attempted_letters = ""
    
    def update_letter_state(self, guessed_letter):
        self.letter_states[guessed_letter] = True
        self.update_show_string()
    
    def check_letter(self, letter):
        """
        Returns whether the letter actually exists.
        """
        return letter in self.letter_states
    
    def is_word_guessed(self):
        return all(self.letter_states.values())
    
    def get_fraction_guessed(self):
        return round(sum(self.letter_states.values())/len(self.letter_states), 2)
    
    def fetch_from_dictionary(self, difficulty):
        self.active_difficulty = difficulty
        
        if self.active_difficulty == 1:
            self.active_word = np.random.choice(easy).upper()
        elif self.active_difficulty == 2:
            self.active_word = np.random.choice(medium).upper()
        elif self.active_difficulty == 3:
            self.active_word = np.random.choice(hard).upper()
        else:
            pass
        
        self.initiate_letter_states()
        self.update_show_string()
    
    def fetch_from_waiting_list(self):
        self.active_word = self.waiting_list.pop(0)
        self.active_word_proposer = self.word_proposer.pop(0)
        self.initiate_letter_states()
    
    def accept_submission(self, word, user_id):
        _word = word.upper()
        self.waiting_list.append(_word)
        self.word_proposer.append(user_id)

class HangmanMultiplayer:
    def __init__(self):
        self.ActiveString = HangmanActiveStringMultiplayer()
        # Initiate state in "dormant"
        self.state = {
            "dormant": True,
            "waiting_for_guess_input": False,
            "waiting_for_submission_input": False
        }
        self.participant_list = {}
        self.scoreboard = {}
        
        self.keyword_join = "/join"
        self.keyword_continue = "/continue"
        
        self.list_of_keywords = [self.keyword_join,
                                 self.keyword_continue]
    
    def change_state(self, state):
        self.state = {i: (i==state) for i, j in self.state.items()}
    
    def start_game(self):
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "A new game of Multiplayer Hangman has been started!"
        ))
        messenger.add_reply(TextSendMessage(
            "Send your words to OA to submit. Accepted words will be played in next rounds. When everyone is done submitting their words, say /continue here."
        ))
        self.change_state("waiting_for_submission_input")
        
        return messenger
    
    def end_game(self):
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "Game is ended!"
        ))
        return messenger
    
    def continue_game(self, received_text):
        messenger = Messenger()
        if received_text = self.keyword_continue:
            messenger.add_reply(TextSendMessage(
                "Guess the words by sending single letter; or guess the entire word by prefixing it with /"
            ))
            messenger.add_reply(TextSendMessage(
                self.ActiveString.get_show_string()
            ))
            self.change_state("waiting_for_guess_input")
        return messenger
    
    def guess(self, received_text, user_id):
        messenger = Messenger()
        received_text = received_text.upper()
        if user_id == self.ActiveString.word_proposer:
            # The proposer is not allowed to guess, return empty Messenger
            return messenger
        
        if received_text.startswith("/"):
            if received_text[1:].upper() == self.ActiveString.active_word:
                messenger.add_reply(TextSendMessage(
                    "Correct! " + received_text + " is the word."
                ))
                messenger.add_reply(TextSendMessage(
                    self.ActiveString.get_show_string()
                ))
                
            else:
                messenger.add_reply(TextSendMessage(
                    "Incorrect! " + received_text + " is not the word."
                ))
                messenger.add_reply(TextSendMessage(
                    self.ActiveString.get_show_string()
                ))
        else:
            if len(received_text) == 1 and received_text.isalpha():
                if received_text in self.ActiveString.attempted_letters:
                    messenger.add_reply(TextSendMessage(
                        "The letter " + received_text + " has been attempted!"
                    ))
                else:
                    self.ActiveString.attempted_letters += received_text
                    if self.ActiveString.check_letter(received_text):
                        self.ActiveString.update_letter_state(received_text)
                        messenger.add_reply(TextSendMessage(
                            "Correct! Letter " + received_text + " is in the word."
                        ))
                        messenger.add_reply(TextSendMessage(
                            self.ActiveString.get_show_string()
                        ))
                    else:
                        messenger.add_reply(TextSendMessage(
                            "Incorrect! Letter " + received_text + " is not in the word."
                        ))
                        messenger.add_reply(TextSendMessage(
                            self.ActiveString.get_show_string()
                        ))
            else:
                pass
            
        if self.ActiveString.is_word_guessed():
            try:
                self.ActiveString.fetch_from_waiting_list()
                messenger.add_reply(TextSendMessage(
                    self.ActiveString.get_show_string()
                ))
            except IndexError as error:
                messenger.add_reply(TextSendMessage(
                    "There is no word left in the waiting list."
                ))
                # The waiting list is empty; what to tell and do here? End the game?
                    
        return messenger
    
    def include_participant(self, received_text, user_id, display_name):
        messenger = Messenger()
        if received_text == self.keyword_join:
            # Consider changing to print participant list instead? To be more intuitive?
            self.participant_list[user_id] = display_name
            self.scoreboard[user_id] = 0
            messenger.add_reply(TextSendMessage(
                display_name + " has joined the game!"
            ))
            messenger.join_game = True
        
        return messenger
    
    def submit_word(self, received_text, user_id):
        messenger = Messenger()
        
            if len([char for char in received_text if char.isalpha()]) < 4:
                messenger.add_reply(TextSendMessage(
                    "Your word is too short. Minimum 4 letters."
                ))
            elif ("/" + received_text.lower()) in self.list_of_keywords:
                messenger.add_reply(TextSendMessage(
                    "Your word is not accepted because it is a keyword. Try another word."
                ))
            else:
                HangmanActiveStringMultiplayer.accept_submission(received_text, user_id)
                messenger.add_reply(TextSendMessage(
                    "Your word " + received_text + " is accepted!"
                ))
                
        return messenger
        
    def parse_and_reply(self, received_text, user_id, display_name, group_id):
        in_personal = (user_id == group_id)
        if self.state["waiting_for_guess_input"] and not in_personal:
            return self.guess(received_text, user_id)
        elif self.state["waiting_for_submission_input"]:
            if in_personal:
                return self.submit_word(received_text, display_name)
            else:
                return self.continue_game(received_text)
        else:
            return Messenger()
        
