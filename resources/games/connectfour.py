import numpy as np
import copy
import timeit
from datetime import timedelta
import json
import os

from ..utils import Messenger

from linebot.models import TextSendMessage, FlexSendMessage

# The default flex board comes from JSON output of LINE Bot Designer.
# Caution: this dict as it is contains plaintext `true`, not True or 'true'.
# Course of action taken: use json.load from file
this_dir, this_filename = os.path.split(__file__)
with open(os.path.join(this_dir, "template_board_flex.json")) as filestream:
    default_flex_board = json.load(filestream)

default_flex_content = default_flex_board["contents"]

class ConnectFourBoard:
    def __init__(self, rows=6, cols=7, empty_tile="."):
        self.rows = rows
        self.cols = cols
        self.empty_tile = empty_tile
        self.mark = ["O","X"]
        self.board = np.empty((self.rows, self.cols), dtype = str)
        self.board[:] = self.empty_tile
        self.tops = {i: self.rows-1 for i in range(self.cols)}
        
        self.last_col = None
    
    def reset(self):
        self.board[:] = self.empty_tile
        self.tops = {i: self.rows-1 for i in range(self.cols)}
    
    def count_empty_tiles(self):
        return np.count_nonzero(self.board == self.empty_tile)
    
    def is_full(self):
        return True if self.count_empty_tiles() == 0 else False
    
    def get_possible_positions(self):
        return {i: j for i, j in self.tops.items() if not j < 0}
    
    def get_board_string(self):
        return '\n'.join([' '.join(self.board[i,:]) for i in range(6)])
    
    def get_board_dict_flex(self):
        board_dict_flex = default_flex_content
        for col in range(self.cols):
            board_dict_flex["body"]["contents"][col]["text"] = '\n'.join(self.board[:,col])
        
        return board_dict_flex
    
    def draw_on_column(self, col, mark):
        board = copy.deepcopy(self)
        board.board[(self.tops[col], col)] = mark
        board.tops[col] -= 1
        board.last_col = col
        return board
    
    def check_last_move_win(self):
        # Checks if last move in last_col result in victory?
        # Is given to Board class instead to allow easier tree search.
        col = self.last_col
        row = self.tops[col] + 1
        mark = self.board[(row, col)]
        
        # Check vertically (down)
        if (row < (self.rows - 3) and
            # Otherwise impossible to have vertical stack of 4
            all([self.board[(i, col)] == mark for i in range(row, row+4)])):
            return True
        
        # Check horizontally
        consecutive_count = 0
        j = 0
        while(j < self.cols and consecutive_count < 4):
            if self.board[(row, j)] == mark:
                consecutive_count += 1
                if consecutive_count == 4:
                    return True
            else:
                consecutive_count = 0
            j += 1
        
        # Check diagonally \
        diag_in_question = np.diag(self.board, col-row)
        if len(diag_in_question) >= 4:
            consecutive_count = 0
            for tile in diag_in_question:
                if tile == mark:
                    consecutive_count += 1
                    if consecutive_count == 4:
                        return True
                else:
                    consecutive_count = 0
        
        # Check diagonally /
        diag_in_question = np.diag(self.board[:, ::-1], (self.cols - 1) - (row + col))
        if len(diag_in_question) >= 4:
            consecutive_count = 0
            for tile in diag_in_question:
                if tile == mark:
                    consecutive_count += 1
                    if consecutive_count == 4:
                        return True
                else:
                    consecutive_count = 0
        
        # Fails all check
        return False

class ConnectFour:
    def __init__(self):
        self.board = ConnectFourBoard()
        self.turn = -1
        self.home_turn_index = None
        self.user_turn_index = None
        self.winner = None
        
        # Initiate state in "dormant"
        self.state = {
            "dormant": True,
            "waiting_for_difficulty_input": False,
            "waiting_for_marker_input": False,
            "waiting_for_column_input": False,
            "waiting_for_restart_input": False
        }
    
    def change_state(self, state):
        self.state = {i: (i==state) for i, j in self.state.items()}
        # Is this good? What if I made typo?
    
    def start_game(self):
        self.board.reset()
        
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "A new game of Connect Four has been started!"
        ))
        
        # Change state from dormant to listening
        self.change_state("waiting_for_difficulty_input")
        
        messenger.add_reply(TextSendMessage(
            "Select difficulty:\n"
            "2 for easy\n"
            "4 for medium\n"
            "6 for hard"
        ))
        
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
                "Not known. Enter yes or no. Do you want to restart the game?"
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
            messenger.add_reply(TextSendMessage(
                "You have set your difficulty to " + str(user_choice)
            ))
            
            self.search_depth = user_choice
            self.change_state("waiting_for_marker_input")

            messenger.add_reply(TextSendMessage(
                "Select marker:\n"
                "Enter 0 to choose O (nought)\n"
                "Enter 1 to choose X (cross)\n"
                "Player with O (nought) goes first."
            ))
        finally:
            return messenger
    
    def set_marker(self, user_choice):
        # Noting at this particular implementation:
        # "The input function should be responsible for multiple try/except" - Stack Overflow
        # to avoid having a nested (and ugly) try/except block here.
        
        messenger = Messenger()
        
        try:
            user_choice = int(user_choice)
        except ValueError as error:
            messenger.add_reply(TextSendMessage(
                "Please input a number, either 0 or 1."
            ))
        else:
            try:
                messenger.add_reply(TextSendMessage(
                    "You choose marker " + str(self.board.mark[user_choice])
                ))
            except IndexError as error:
                messenger.add_reply(TextSendMessage(
                    "Please input either 0 or 1."
                ))
            else:
                self.user_turn_index = user_choice
                self.home_turn_index = 1 - user_choice
                
                if user_choice == 1:
                    messenger.add_replies(self.home_turn().reply_array)
                else:
                    messenger.add_reply(FlexSendMessage(
                        alt_text = "User_turn_board",
                        contents = self.board.get_board_dict_flex()
                    ))
                
                self.change_state("waiting_for_column_input")
        finally:
            return messenger
    
    def home_turn(self):
        messenger = Messenger()
        start_time = timeit.default_timer()
        col = self.choose_best_move()
        end_time = timeit.default_timer()
        # Draw using mark[home], then
        # Check if that was victory
        self.board = self.board.draw_on_column(col, self.board.mark[self.home_turn_index])
        messenger.add_reply(FlexSendMessage(
            alt_text = "Home_turn_board",
            contents = self.board.get_board_dict_flex()
        ))
        messenger.add_reply(TextSendMessage(
            "Time taken to think: " + str(timedelta(seconds = end_time - start_time)) + "\n" +
            "Computer decides to move at column " + str(col + 1) + "." + "\n" +
            "Enter column you decide to move at!"
        ))
        if self.board.check_last_move_win():
            messenger.add_reply(TextSendMessage(
                "You lose!\n"
                "Do you want to play again? Yes/No"
            ))
            self.change_state("waiting_for_restart_input")
        
        return messenger
    
    def user_turn(self, col):
        messenger = Messenger()
        # Draw using mark[user], then
        # Check if that was victory
        try:
            col = int(col)-1
        except ValueError as error:
            messenger.add_reply(TextSendMessage(
                "Not a valid numeric value."
            ))
        else:
            if col in self.board.get_possible_positions():
                try:
                    self.board = self.board.draw_on_column(col, self.board.mark[self.user_turn_index])
                except KeyError as error:
                    messenger.add_reply(
                        "Not a valid column number."
                    )
                else:
                    messenger.add_reply(FlexSendMessage(
                        alt_text = "User_turn_board",
                        contents = self.board.get_board_dict_flex()
                    ))
                    messenger.add_reply(TextSendMessage(
                        "You decide to move at column " + str(col+1) + "."
                    ))
                    if self.board.check_last_move_win():
                        messenger.add_reply(TextSendMessage(
                            "You win!\n"
                            "Do you want to play again? Yes/No"
                        ))
                        self.change_state("waiting_for_restart_input")
                    else:
                        messenger.add_replies(self.home_turn().reply_array)
            else:
                messenger.add_reply(TextSendMessage(
                    "Illegal column chosen."
                ))
                
        return messenger
    
    # Current implementation problems:
    
    # If CPU has two winning alternatives, the CPU will go to "random"
    # because "it will win whatsoever".
    def get_node_score(self, depth, board, alpha, beta):
        if depth % 2 == 0:
            if board.check_last_move_win():
                return depth
            
            if depth == 1:
                return 0
            
            mark = self.board.mark[self.user_turn_index]
            possible_moves = list(board.get_possible_positions().keys())
            possible_moves = np.random.choice(possible_moves, len(possible_moves), replace=False)
            child_node_scores = []
            for move in possible_moves:
                value = self.get_node_score(depth-1, board.draw_on_column(move, mark), alpha, beta)
                if value > alpha:
                    alpha = value
                    child_node_scores = []
                child_node_scores.append(value)
                if alpha > beta:
                    break
            return np.min(child_node_scores)
        
        else:
            if board.check_last_move_win():
                return -depth
            
            if depth == 1:
                return 0
            
            
            mark = self.board.mark[self.user_turn_index]
            possible_moves = list(board.get_possible_positions().keys())
            possible_moves = np.random.choice(possible_moves, len(possible_moves), replace=False)
            child_node_scores = []
            for move in possible_moves:
                value = self.get_node_score(depth-1, board.draw_on_column(move, mark), alpha, beta)
                if value < beta:
                    beta = value
                    child_node_scores = []
                child_node_scores.append(value)
                if beta < alpha:
                    break
            return np.max(child_node_scores)
    
    def choose_best_move(self):
        move_value = {col: self.get_node_score(
                           self.search_depth,
                           self.board.draw_on_column(col, self.board.mark[self.home_turn_index]),
                           -self.search_depth-1, self.search_depth+1)
                      for col in self.board.get_possible_positions()}    
        
        max_value = np.max(list(move_value.values()))
        max_value_moves = [i for i in move_value if move_value[i] == max_value]
        return np.random.choice(max_value_moves)
    
    def parse_and_reply(self, received_text, user_id, display_name, group_id):
        """
        Take received_text string.
        Should return an array of string.
        """
        
        if self.state["waiting_for_difficulty_input"]:
            return self.set_difficulty(received_text)
        elif self.state["waiting_for_marker_input"]:
            return self.set_marker(received_text)
        elif self.state["waiting_for_column_input"]:
            return self.user_turn(received_text)
        elif self.state["waiting_for_restart_input"]:
            return self.restart_game(received_text)
