"""
Othello (Reversi) game logic.
Board coordinates: (row, col), 0-indexed, top-left is (0, 0).
BLACK = 1 (player), WHITE = -1 (AI).
"""

import numpy as np
from typing import List, Tuple, Optional

EMPTY = 0
BLACK = 1
WHITE = -1

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


class OthelloGame:
    def __init__(self):
        self.board = np.zeros((8, 8), dtype=int)
        # Standard starting position
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE
        self.current_player = BLACK

    def is_valid_move(self, row: int, col: int, player: int) -> bool:
        if not (0 <= row < 8 and 0 <= col < 8):
            return False
        if self.board[row][col] != EMPTY:
            return False
        for dr, dc in DIRECTIONS:
            r, c = row + dr, col + dc
            found_opponent = False
            while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == -player:
                found_opponent = True
                r, c = r + dr, c + dc
            if found_opponent and 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == player:
                return True
        return False

    def get_valid_moves(self, player: int) -> List[Tuple[int, int]]:
        return [
            (r, c)
            for r in range(8)
            for c in range(8)
            if self.is_valid_move(r, c, player)
        ]

    def apply_move(self, row: int, col: int, player: int) -> "OthelloGame":
        """Return a new game state after placing a piece."""
        new_game = OthelloGame.__new__(OthelloGame)
        new_game.board = self.board.copy()
        new_game.current_player = -player  # switch turn
        new_game.board[row][col] = player

        for dr, dc in DIRECTIONS:
            flips = []
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8 and new_game.board[r][c] == -player:
                flips.append((r, c))
                r, c = r + dr, c + dc
            if flips and 0 <= r < 8 and 0 <= c < 8 and new_game.board[r][c] == player:
                for fr, fc in flips:
                    new_game.board[fr][fc] = player

        return new_game

    def get_score(self) -> Tuple[int, int]:
        """Returns (black_count, white_count)."""
        black = int(np.sum(self.board == BLACK))
        white = int(np.sum(self.board == WHITE))
        return black, white

    def is_game_over(self) -> bool:
        return (
            len(self.get_valid_moves(BLACK)) == 0
            and len(self.get_valid_moves(WHITE)) == 0
        )

    def get_winner(self) -> Optional[int]:
        if not self.is_game_over():
            return None
        black, white = self.get_score()
        if black > white:
            return BLACK
        if white > black:
            return WHITE
        return EMPTY  # Draw
