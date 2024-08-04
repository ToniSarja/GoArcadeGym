import arcade
import numpy as np
import itertools
import networkx as nx
from line_draw import *
from stable_baselines3 import PPO


SCREEN_WIDTH = 575
SCREEN_HEIGHT = 575
BOARD_WIDTH = 500
BOARD_BORDER = 25
size = 9
DOT_RADIUS = 5
SCREEN_TITLE = "Go Game"
STONE_RADIUS = 22
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

#env = GoEnv(size=9)

# Load the model
model = PPO.load("go_ppo_agent9x9")


def make_grid(size):
    """Return list of (start_point, end_point pairs) defining gridlines"""
    start_points, end_points = [], []

    # vertical start points (constant y)
    xs = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size)
    ys = np.full((size), BOARD_BORDER)
    start_points += list(zip(xs, ys))

    # horizontal start points (constant x)
    xs = np.full((size), BOARD_BORDER)
    ys = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size)
    start_points += list(zip(xs, ys))

    # vertical end points (constant y)
    xs = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size)
    ys = np.full((size), BOARD_WIDTH - BOARD_BORDER)
    end_points += list(zip(xs, ys))

    # horizontal end points (constant x)
    xs = np.full((size), BOARD_WIDTH - BOARD_BORDER)
    ys = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size)
    end_points += list(zip(xs, ys))

    return start_points, end_points

def xy_to_colrow(x, y, size):
    """Convert x,y coordinates to column and row number"""
    inc = (BOARD_WIDTH - 2 * BOARD_BORDER) / (size - 1)
    x_dist = x - BOARD_BORDER
    y_dist = y - BOARD_BORDER
    col = int(round(x_dist / inc))
    row = int(round(y_dist / inc))
    return col, row

def colrow_to_xy(col, row, size):
    """Convert column and row numbers to x,y coordinates"""
    inc = (BOARD_WIDTH - 2 * BOARD_BORDER) / (size - 1)
    x = int(BOARD_BORDER + col * inc)
    y = int(BOARD_BORDER + row * inc)
    return x, y

class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.board = np.zeros((size, size))  # Game board initialized as a grid of zeros
        self.previous_board = None  # To store the board state before the current move (for Ko rule)
        self.black_turn = True  # To track whose turn it is (True for black, False for white)
        self.prisoners = {"black": 0, "white": 0}  # To keep count of captured stones
        arcade.set_background_color(arcade.color.WOOD_BROWN)

    def setup(self):
        pass

    def has_no_liberties(self, board, group):
        """Checks if a given group of stones has no liberties (i.e., empty adjacent spaces)."""
        for x, y in group:
            if x > 0 and board[x - 1, y] == 0:  # Check above
                return False
            if y > 0 and board[x, y - 1] == 0:  # Check left
                return False
            if x < board.shape[0] - 1 and board[x + 1, y] == 0:  # Check below
                return False
            if y < board.shape[0] - 1 and board[x, y + 1] == 0:  # Check right
                return False
        return True

    def on_draw(self):
        """Handles drawing the board, stones, and grid lines on the screen."""
        self.clear()
        start_points, end_points = make_grid(size)
        for start_point, end_point in zip(start_points, end_points):
            arcade.draw_line(start_point[0], start_point[1], end_point[0], end_point[1], arcade.color.BLACK, 2)

        # Draw guide dots for 9x9 board
        guide_dots = [2, size // 2, size - 3]
        for col, row in itertools.product(guide_dots, guide_dots):
            x, y = colrow_to_xy(col, row, size)
            arcade.draw_circle_filled(x, y, DOT_RADIUS, arcade.color.BLACK)

        # Draw black stones
        for col, row in zip(*np.where(self.board == 1)):
            x, y = colrow_to_xy(col, row, size)
            arcade.draw_circle_filled(x, y, STONE_RADIUS, arcade.color.BLACK)

        # Draw white stones
        for col, row in zip(*np.where(self.board == 2)):
            x, y = colrow_to_xy(col, row, size)
            arcade.draw_circle_filled(x, y, STONE_RADIUS, arcade.color.WHITE)

    def get_stone_groups(self, board, color):
        """Identifies and returns all groups of connected stones of the specified color."""
        color_code = 1 if color == "black" else 2  # 1 for black, 2 for white
        xs, ys = np.where(board == color_code)  # Find all positions with the current color
        size = board.shape[0]
        graph = nx.grid_graph(dim=[size, size])  # Create a grid graph for the board
        stones = set(zip(xs, ys))  # Set of all stones of the current color
        all_spaces = set(itertools.product(range(size), range(size)))  # All possible board positions
        stones_to_remove = all_spaces - stones  # Positions without stones of the current color
        graph.remove_nodes_from(stones_to_remove)  # Remove positions without stones
        return list(nx.connected_components(graph))  # Return the connected components (stone groups)

    def is_valid_move(self, col, row, board):
        """Determines if placing a stone at the specified position is a valid move."""
        if col < 0 or col >= board.shape[0] or row < 0 or row >= board.shape[0]:
            return False  # Move is outside the board boundaries
        if board[col, row] != 0:
            return False  # Move is on an already occupied spot

        # Simulate the move to check if it violates the suicide rule
        temp_board = board.copy()
        temp_board[col, row] = 1 if self.black_turn else 2  # Place the stone
        color = "black" if self.black_turn else "white"
        group = None
        for group in self.get_stone_groups(temp_board, color):
            if (col, row) in group:
                break
        if self.has_no_liberties(temp_board, group):
            return False  # Move is invalid due to suicide rule

        return True

    def on_mouse_press(self, x, y, button, key_modifiers):
        """Handles the logic when a player clicks on the board to place a stone."""
        col, row = xy_to_colrow(x, y, size)

        if self.black_turn:
            # Human player's move
            if not self.is_valid_move(col, row, self.board):
                return  # If the move is invalid, do nothing

            # Save the current board state before making the move (for Ko rule check)
            self.previous_board = self.board.copy()
            self.board[col, row] = 1  # Place black stone

            # Check for captures
            opponent_color = "white"
            for group in self.get_stone_groups(self.board, opponent_color):
                if self.has_no_liberties(self.board, group):
                    for i, j in group:
                        self.board[i, j] = 0
                    self.prisoners[opponent_color] += len(group)

            # Ko rule check
            if np.array_equal(self.board, self.previous_board):
                self.board[col, row] = 0  # Undo the move
                return

            # Switch turns
            self.black_turn = False  # Next turn is for white (AI)

        else:
            # AI's move
            action, _ = model.predict(self.board)
            row, col = divmod(action, size)

            if self.is_valid_move(col, row, self.board):
                self.previous_board = self.board.copy()  # Save state before AI move
                self.board[row, col] = 2  # Place white stone

                # Check for captures
                opponent_color = "black"
                for group in self.get_stone_groups(self.board, opponent_color):
                    if self.has_no_liberties(self.board, group):
                        for i, j in group:
                            self.board[i, j] = 0
                        self.prisoners[opponent_color] += len(group)

                # Ko rule check
                if np.array_equal(self.board, self.previous_board):
                    self.board[row, col] = 0  # Undo the move
                    return

                # Switch turns
                self.black_turn = True  # Next turn is for black (human)

        # Redraw the board after the move
        self.on_draw()

def main():
    game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()
