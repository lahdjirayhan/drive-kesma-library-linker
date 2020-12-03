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

class HangmanActiveString:
    def __init__(self):
        self.active_difficulty = None
        self.active_word = ""
        self.letter_states = {}
        self.show_string = ""
        self.attempted_letters = ""
    
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
    
    def fetch_next_word(self, difficulty):
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

class Hangman:
    def __init__(self, allowed_wrongs=9):
        self.ActiveString = HangmanActiveString()
        self.allowed_wrongs = allowed_wrongs
        # Initiate state in "dormant"
        self.state = {
            "dormant": True,
            "waiting_for_difficulty_input": False,
            "waiting_for_guess_input": False,
            "waiting_for_restart_input": False
        }
    
    def change_state(self, state):
        self.state = {i: (i==state) for i, j in self.state.items()}
    
    def start_game(self):
        self.player_score = 0
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "A new game of Hangman has been started!"
        ))
        messenger.add_reply(TextSendMessage(
            "Select difficulty for your first word:\n"
            "1 for easy\n"
            "2 for medium\n"
            "3 for hard"
        ))
        self.change_state("waiting_for_difficulty_input")
        
        return messenger
    
    def restart_game(self, user_choice):
        messenger = Messenger()
        if user_choice.lower() == "yes":
            messenger.add_replies(self.start_game().reply_array)
        elif user_choice.lower() == "no":
            messenger.add_reply(TextSendMessage(
                "Game is ended. Will be dormant and not listening."
            ))
            self.change_state("dormant")
            messenger.end_game = True
        else:
            messenger.add_reply(TextSendMessage(
                "Input not known. Enter yes or no. Do you want to restart the game?"
            ))
        
        return messenger 
    
    def end_game(self):
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "Game is ended. Will be dormant and not listening."
        ))
        
        # Change state from listening to dormant.
        self.change_state("dormant")
        return messenger
    
    def set_difficulty(self, user_choice):
        messenger = Messenger()
        
        try:
            user_choice = abs(int(user_choice))
        except ValueError as error:
            messenger.add_reply(TextSendMessage(
                "Please input a positive number."
            ))
        else:
            self.ActiveString.fetch_next_word(user_choice)
            messenger.add_reply(TextSendMessage(
                "You have set your difficulty to " + str(user_choice)
            ))
            
            messenger.add_reply(TextSendMessage(
                self.ActiveString.get_show_string() + ("\n"
                "Allowed wrongs: " + str(self.allowed_wrongs))
            ))
            
            self.change_state("waiting_for_guess_input")
            
        finally:
            return messenger
    
    def guess(self, received_text):
        messenger = Messenger()
        
        received_text = received_text.upper()
        if len(received_text) != 1:
            messenger.add_reply(TextSendMessage(
                "Please guess one letter at a time."
            ))
            return messenger
        elif not received_text.isalpha():
            messenger.add_reply(TextSendMessage(
                "Please enter only a letter as your guess."
            ))
            return messenger
        elif received_text in self.ActiveString.attempted_letters:
            messenger.add_reply(TextSendMessage(
                "You have guessed this letter before."
            ))
        elif not self.ActiveString.check_letter(received_text):
            messenger.add_reply(TextSendMessage(
                "Wrong guess!"
            ))
            self.ActiveString.attempted_letters += received_text
            self.allowed_wrongs -= 1    
        else:
            self.ActiveString.attempted_letters += received_text
            self.ActiveString.update_letter_state(received_text)
        
        messenger.add_reply(TextSendMessage(
            self.ActiveString.get_show_string() + ("\n"
            "Allowed wrongs: " + str(self.allowed_wrongs))
        ))
        
        if self.allowed_wrongs == 0:
            self.player_score += (self.ActiveString.get_fraction_guessed() *
                                  self.ActiveString.active_difficulty *
                                  10)
            self.ActiveString.letter_states = {k: True for k in self.ActiveString.letter_states}
            self.ActiveString.update_show_string()
            
            messenger.add_reply(TextSendMessage(
                ("Game over!\n" +
                 "The correct word is:\n" +
                 self.ActiveString.get_show_string() + "\n" +
                 "\n" +
                 "Your score is " + str(self.player_score) + "\n" +
                 "\n"
                 "Do you want to play again? Yes/No")
            ))
            self.change_state("waiting_for_restart_input")
        
        elif self.ActiveString.is_word_guessed():
            self.player_score += (self.ActiveString.active_difficulty *
                                  10)
            self.allowed_wrongs += 2
            
            messenger.add_reply(TextSendMessage(
                ("Nice answer!\n" +
                 "Your score is " + str(self.player_score) + "\n" +
                 "\n"
                 "Your allowed wrongs have been added by 2.\n" +
                 "Allowed wrongs = " + str(self.allowed_wrongs))
            ))
            messenger.add_reply(TextSendMessage(
                "Select difficulty for your next word:\n"
                "1 for easy\n"
                "2 for medium\n"
                "3 for hard"
            ))
            self.change_state("waiting_for_difficulty_input")
        
        return messenger
    
    def parse_and_reply(self, received_text, user_id, display_name, group_id):
        if self.state["waiting_for_difficulty_input"]:
            return self.set_difficulty(received_text)
        elif self.state["waiting_for_guess_input"]:
            return self.guess(received_text)
        elif self.state["waiting_for_restart_input"]:
            return self.restart_game(received_text)
