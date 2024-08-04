import arcade
import numpy as np
import itertools
import networkx as nx
import gymnasium as gym

SCREEN_WIDTH = 300  # Adjust screen size for smaller board
SCREEN_HEIGHT = 300  # Adjust screen size for smaller board
BOARD_WIDTH = 250
BOARD_BORDER = 25
size = 9  # Change board size to 9x9
DOT_RADIUS = 4
STONE_RADIUS = 22
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SCREEN_TITLE = "Go Game"

class GoEnv(gym.Env):
    def __init__(self, size=9):  # Set the size to 9 for a 9x9 board
        super(GoEnv, self).__init__()
        self.size = size
        self.board = np.zeros((size, size), dtype=int)  # Use a 2D array for the board
        self.action_space = gym.spaces.Discrete(size * size)
        self.observation_space = gym.spaces.Box(low=0, high=2, shape=(size, size), dtype=int)  # Set observation space to 9x9

    def reset(self, seed=None):
        self.board = np.zeros((self.size, self.size), dtype=int)  # Return a 2D board
        return self.board, {}

    def step(self, action):
        row, col = divmod(action, self.size)
        reward = 0
        terminated = False
        truncated = False
        info = {}

        # Your game logic here...

        return self.board, reward, terminated, truncated, info  # Return a 2D board

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
