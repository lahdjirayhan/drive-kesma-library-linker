import numpy as np
import copy
import timeit
from datetime import timedelta
import json
import os
from ast import literal_eval

from ..utils import Messenger

from linebot.models import TextSendMessage, FlexSendMessage

this_dir, this_filename = os.path.split(__file__)
with open(os.path.join(this_dir, "template_tictactoe_3x3_board.json")) as filestream:
    default_flex_content = json.load(filestream)

class TictactoeBoard:
    def __init__(self, size = 3, win_length = 3, empty_tile = "."):
        self.size = size
        self.win_length = win_length
        self.mark = ["O", "X"]
        self.empty_tile = empty_tile
        
        self.board = np.empty((self.size, self.size), dtype = str)
        self.board[:] = self.empty_tile
        
        self.last_tile = None
    
    def reset(self):
        self.board[:] = self.empty_tile
        self.last_tile = None
    
    def count_empty_tiles(self):
        return np.count_nonzero(self.board == self.empty_tile)
    
    def get_possible_positions(self):
        # Note: don't pick all, pick random subset
        return [tuple(np.array(np.where(self.board==self.empty_tile)).T[i])
                for i in range(self.count_empty_tiles())]
    
    def get_board_string(self):
        return '\n'.join([' '.join(self.board[i,:]) for i in range(self.size)])
    
    def get_board_dict_flex(self):
        board_dict_flex = default_flex_content
        for i in range(self.size):
            for j in range(self.size):
                board_dict_flex["body"]["contents"][i]["contents"][j]["text"] = self.board[(i,j)]
        return board_dict_flex
    
    def draw_on_tile(self, tile, mark):
        board = copy.deepcopy(self)
        board.board[tile] = mark
        board.last_tile = tile
        return board
    
    def check_last_move_win(self):
        # Checks if last move in last_col result in victory?
        # Is given to Board class instead to allow easier tree search.
        row = self.last_tile[0]
        col = self.last_tile[1]
        mark = self.board[self.last_tile]
        
        # Check vertically (down)
        # Not using "if all are same marker" to allow expanding to larger grid
        consecutive_count = 0
        for i in range(self.size):
            if self.board[(i, col)] == mark:
                consecutive_count += 1
                if consecutive_count == self.win_length:
                    return True
            else:
                consecutive_count = 0
        
        # Check horizontally
        consecutive_count = 0
        for j in range(self.size):
            if self.board[(row, j)] == mark:
                consecutive_count += 1
                if consecutive_count == self.win_length:
                    return True
            else:
                consecutive_count = 0
        
        # Check diagonally \
        diag_in_question = np.diag(self.board, col-row)
        if len(diag_in_question) >= self.win_length:
            consecutive_count = 0
            for tile in diag_in_question:
                if tile == mark:
                    consecutive_count += 1
                    if consecutive_count == self.win_length:
                        return True
                else:
                    consecutive_count = 0
        
        # Check diagonally /
        diag_in_question = np.diag(self.board[:, ::-1], (self.size - 1) - (row + col))
        if len(diag_in_question) >= self.win_length:
            consecutive_count = 0
            for tile in diag_in_question:
                if tile == mark:
                    consecutive_count += 1
                    if consecutive_count == self.win_length:
                        return True
                else:
                    consecutive_count = 0
        
        # Fails all check
        return False


class Tictactoe:
    def __init__(self):
        self.board = TictactoeBoard()
        self.turn = 0
        self.home_turn_index = None
        self.user_turn_index = None
        self.winner = None
        self.search_depth = 8   # Fixed, no difficulty levels
        
        # Initiate state in "dormant"
        self.state = {
            "dormant": True,
            "waiting_for_marker_input": False,
            "waiting_for_tile_input": False,
            "waiting_for_restart_input": False
        }
    
    def change_state(self, state):
        self.state = {i: (i==state) for i, j in self.state.items()}
    
    def start_game(self):
        self.board.reset()
        
        messenger = Messenger()
        messenger.add_reply(TextSendMessage(
            "A new game of Tictactoe has been started!"
        ))
        
        messenger.add_reply(TextSendMessage(
            "Select marker:\n"
            "Enter 0 to choose O (nought)\n"
            "Enter 1 to choose X (cross)\n"
            "Player with O (nought) goes first."
        ))
        
        # Change state from dormant to listening
        self.change_state("waiting_for_marker_input")
        
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
    
    def set_marker(self, user_choice):
        messenger = Messenger()
        
        try:
            user_choice = int(user_choice)
        except ValueError as error:
            messenger.add_reply(TextSendMessage(
                "Please input a number, either 0 or 1."
            ))
            return messenger
        
        try:
            messenger.add_reply(TextSendMessage(
                "You choose marker " + str(self.board.mark[user_choice])
            ))
        except IndexError as error:
            messenger.add_reply(TextSendMessage(
                "Please input either 0 or 1."
            ))
            return messenger
        
        self.user_turn_index = user_choice
        self.home_turn_index = 1 - user_choice
        
        if user_choice == 1:
            messenger.add_replies(self.home_turn().reply_array)
        else:
            messenger.add_reply(FlexSendMessage(
                alt_text = "User_turn_board",
                contents = self.board.get_board_dict_flex()
            ))
            messenger.add_reply(TextSendMessage(
                "Tap at the empty tile on above chat to move!"
            ))
        self.change_state("waiting_for_tile_input")
        
        return messenger
    
    def home_turn(self):
        messenger = Messenger()
        start_time = timeit.default_timer()
        tile = self.choose_best_move()
        end_time = timeit.default_timer()
        # Draw using mark[home], then
        # Check if that was victory
        self.board = self.board.draw_on_tile(tile, self.board.mark[self.home_turn_index])
        self.turn += 1
        messenger.add_reply(FlexSendMessage(
            alt_text = "Home_turn_board",
            contents = self.board.get_board_dict_flex()
        ))
        messenger.add_reply(TextSendMessage(
            "Time taken to think: " + str(timedelta(seconds = end_time - start_time)) + "\n" +
            "Computer decides to move at tile " + str(tuple(i+1 for i in tile)) + "." + "\n" +
            "Tap at the empty tile on above chat to move!"
        ))
        if self.board.check_last_move_win():
            messenger.add_reply(TextSendMessage(
                "You lose!\n"
                "Do you want to play again? Yes/No"
            ))
            self.change_state("waiting_for_restart_input")
        elif self.board.count_empty_tiles() == 0:
            messenger.add_reply(TextSendMessage(
                "It's a tie!\n"
                "Do you want to play again? Yes/No"
            ))
            self.change_state("waiting_for_restart_input")
        
        return messenger
    
    def user_turn(self, received_text):
        """
        Expects a string like 1,2 or (1,2) to then be made tuple
        by ast.literal_eval
        """
        messenger = Messenger()
        try:
            tile = literal_eval(received_text)
        except ValueError as e:
            messenger.add_reply(TextSendMessage(
                "Not a valid tile position."
            ))
        
        if not isinstance(tile, tuple):
            messenger.add_reply(TextSendMessage(
                "Not a valid tile position."
            ))
            return messenger
        
        if len(tile) != 2:
            messenger.add_reply(TextSendMessage(
                "Not a valid tile position."
            ))
            return messenger
        
        tile = tuple([i-1 for i in tile])
        
        if tile[0] not in range(self.board.size) or tile[1] not in range(self.board.size):
            messenger.add_reply(TextSendMessage(
                "Out of bound tile position."
            ))
            return messenger
        
        if tile not in self.board.get_possible_positions():
            messenger.add_reply(TextSendMessage(
                "Not an empty tile position."
            ))
            return messenger
        
        self.board = self.board.draw_on_tile(tile, self.board.mark[self.user_turn_index])
        self.turn += 1
        if self.board.check_last_move_win():
            messenger.add_reply(TextSendMessage(
                "You win!\n"
                "Do you want to play again? Yes/No"
            ))
            self.change_state("waiting_for_restart_input")
        elif self.board.count_empty_tiles() == 0:
            messenger.add_reply(TextSendMessage(
                "It's a tie!\n"
                "Do you want to play again? Yes/No"
            ))
            self.change_state("waiting_for_restart_input")
        else:
            messenger.add_replies(self.home_turn().reply_array)
        
        return messenger
    
    def get_node_score(self, depth, board, alpha, beta):
        if depth % 2 == 0:
            if board.check_last_move_win():
                return depth
            
            if depth < 1:
                return 0
            
            possible_moves = board.get_possible_positions()
            
            if len(possible_moves) == 0:
                return 0
            
            np.random.shuffle(possible_moves)
            mark = self.board.mark[self.user_turn_index]
            child_node_scores = []
            for move in possible_moves:
                value = self.get_node_score(depth-1, board.draw_on_tile(move, mark), alpha, beta)
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
            
            if depth < 1:
                return 0
            
            possible_moves = board.get_possible_positions()
            
            if len(possible_moves) == 0:
                return 0
            
            np.random.shuffle(possible_moves)
            mark = self.board.mark[self.home_turn_index]
            child_node_scores = []
            for move in possible_moves:
                value = self.get_node_score(depth-1, board.draw_on_tile(move, mark), alpha, beta)
                if value < beta:
                    beta = value
                    child_node_scores = []
                child_node_scores.append(value)
                if beta < alpha:
                    break
            return np.max(child_node_scores)
    
    def choose_best_move(self):
        """
        Returns tuple.
        """
        # Determines first move of first player
        if self.turn == 0:
            random_number = np.random.uniform()
            if random_number < 0.3:
                corners = [(0, 0),
                           (0, self.board.size-1),
                           (self.board.size-1, 0),
                           (self.board.size-1, self.board.size-1)]
                return corners[np.random.choice(4)]
            
            return (1,1)    # Middle on 3x3, lazy patch/fix
            
        # Will return tuple corners with 90% prob in case of the first move of second player
        if self.turn == 1 and np.random.uniform() < 0.9:        
            corners = [(0, 0),
                       (0, self.board.size-1),
                       (self.board.size-1, 0),
                       (self.board.size-1, self.board.size-1)]
            choice = np.random.choice(4)
            while self.board.board[corners[choice]] != self.board.empty_tile:
                choice = np.random.choice(4)
            return corners[choice]
        
        move_value = {tile: self.get_node_score(
                            self.search_depth,
                            self.board.draw_on_tile(tile, self.board.mark[self.home_turn_index]),
                            -self.search_depth-1, self.search_depth+1)
                      for tile in self.board.get_possible_positions()}    
        
        max_value = np.max(list(move_value.values()))
        max_value_moves = [i for i in move_value if move_value[i] == max_value]
        return max_value_moves[np.random.choice(len(max_value_moves))]
    
    def parse_and_reply(self, received_text, user_id, display_name, group_id):
        """
        Take received_text string.
        Should return an array of string.
        """
        if self.state["waiting_for_marker_input"]:
            return self.set_marker(received_text)
        elif self.state["waiting_for_tile_input"]:
            return self.user_turn(received_text)
        elif self.state["waiting_for_restart_input"]:
            return self.restart_game(received_text)
