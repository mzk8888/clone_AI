"""
AI player for Othello using Minimax with Alpha-Beta pruning.
Evaluation function considers:
  - Positional weights (corners are most valuable)
  - Mobility (number of available moves)
  - Coin parity (piece count difference)
  - Corner ownership
"""

import numpy as np
from typing import Optional, Tuple

from game import BLACK, WHITE, EMPTY, OthelloGame

# Positional weight table — corners are extremely valuable
POSITION_WEIGHTS = np.array([
    [120, -20,  20,  5,  5,  20, -20, 120],
    [-20, -40,  -5, -5, -5,  -5, -40, -20],
    [ 20,  -5,  15,  3,  3,  15,  -5,  20],
    [  5,  -5,   3,  3,  3,   3,  -5,   5],
    [  5,  -5,   3,  3,  3,   3,  -5,   5],
    [ 20,  -5,  15,  3,  3,  15,  -5,  20],
    [-20, -40,  -5, -5, -5,  -5, -40, -20],
    [120, -20,  20,  5,  5,  20, -20, 120],
], dtype=float)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]


class OthelloAI:
    def __init__(self, depth: int = 5):
        self.depth = depth

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, game: OthelloGame, player: int) -> float:
        board = game.board
        score = 0.0

        # 1. Positional score
        score += float(np.sum(board * POSITION_WEIGHTS)) * player

        # 2. Mobility
        my_moves = len(game.get_valid_moves(player))
        opp_moves = len(game.get_valid_moves(-player))
        denom = my_moves + opp_moves
        if denom > 0:
            score += 30.0 * (my_moves - opp_moves) / denom

        # 3. Coin parity (weighted more in endgame)
        black, white = game.get_score()
        total = black + white
        parity = (black - white) * player
        weight = 10.0 if total < 50 else 30.0
        score += weight * parity / max(total, 1)

        # 4. Corner stability
        corner_score = sum(board[r][c] for r, c in CORNERS) * player
        score += 25.0 * corner_score

        return score

    # ------------------------------------------------------------------
    # Minimax with Alpha-Beta
    # ------------------------------------------------------------------

    def _minimax(
        self,
        game: OthelloGame,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        player: int,
    ) -> Tuple[float, Optional[Tuple[int, int]]]:
        if depth == 0 or game.is_game_over():
            return self._evaluate(game, player), None

        current = player if maximizing else -player
        moves = game.get_valid_moves(current)

        if not moves:
            # No moves — pass the turn
            val, _ = self._minimax(game, depth - 1, alpha, beta, not maximizing, player)
            return val, None

        best_move = None

        if maximizing:
            best_val = float("-inf")
            for move in moves:
                new_game = game.apply_move(move[0], move[1], current)
                val, _ = self._minimax(new_game, depth - 1, alpha, beta, False, player)
                if val > best_val:
                    best_val = val
                    best_move = move
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = float("inf")
            for move in moves:
                new_game = game.apply_move(move[0], move[1], current)
                val, _ = self._minimax(new_game, depth - 1, alpha, beta, True, player)
                if val < best_val:
                    best_val = val
                    best_move = move
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_best_move(
        self, game: OthelloGame, player: int
    ) -> Optional[Tuple[int, int]]:
        _, move = self._minimax(
            game, self.depth, float("-inf"), float("inf"), True, player
        )
        return move
