from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from .game_state import GameState, Move
from .constants import PLAYER_WHITE, PLAYER_BLACK


@dataclass
class AIDifficulty:
	name: str
	depth: int
	use_alpha_beta: bool
	allow_random: bool = False


EASY = AIDifficulty("Easy", depth=1, use_alpha_beta=False, allow_random=True)
MEDIUM = AIDifficulty("Medium", depth=3, use_alpha_beta=True)
HARD = AIDifficulty("Hard", depth=5, use_alpha_beta=True)


def evaluate(state: GameState, maximizing_player: int) -> float:
	# Basic heuristic combining: pieces, mobility, mills potential
	opponent = -maximizing_player
	my_pieces = state.num_pieces(maximizing_player)
	opp_pieces = state.num_pieces(opponent)
	if state.winner == maximizing_player:
		return 10_000.0
	if state.winner == opponent:
		return -10_000.0
	# Mobility (approximate): number of legal moves when it is player's turn if we simulate
	# We compute mobility by temporarily toggling turn
	current_to_move = state.to_move
	state.to_move = maximizing_player
	my_moves = len(state.legal_moves())
	state.to_move = opponent
	opp_moves = len(state.legal_moves())
	state.to_move = current_to_move
	value = 0.0
	value += 100.0 * (my_pieces - opp_pieces)
	value += 2.0 * (my_moves - opp_moves)
	# Prefer exiting placing sooner (material on board)
	value += 1.0 * (9 - (state.white_in_hand if maximizing_player == PLAYER_WHITE else state.black_in_hand))
	return value


def minimax(state: GameState, depth: int, alpha: float, beta: float, maximizing_player: int, use_alpha_beta: bool) -> Tuple[float, Optional[Move]]:
	if depth == 0 or state.winner is not None:
		return evaluate(state, maximizing_player), None
	moves = state.legal_moves()
	if not moves:
		# No legal moves -> gameover for current player
		clone = state.clone()
		clone.winner = -clone.to_move
		return evaluate(clone, maximizing_player), None
	best_move: Optional[Move] = None
	if state.to_move == maximizing_player:
		best_val = -math.inf
		for mv in moves:
			child = state.clone()
			child.apply_move(mv)
			val, _ = minimax(child, depth - 1, alpha, beta, maximizing_player, use_alpha_beta)
			if val > best_val:
				best_val = val
				best_move = mv
			if use_alpha_beta:
				alpha = max(alpha, best_val)
				if beta <= alpha:
					break
		return best_val, best_move
	else:
		best_val = math.inf
		for mv in moves:
			child = state.clone()
			child.apply_move(mv)
			val, _ = minimax(child, depth - 1, alpha, beta, maximizing_player, use_alpha_beta)
			if val < best_val:
				best_val = val
				best_move = mv
			if use_alpha_beta:
				beta = min(beta, best_val)
				if beta <= alpha:
					break
		return best_val, best_move


def choose_move(state: GameState, difficulty: AIDifficulty) -> Optional[Move]:
	moves = state.legal_moves()
	if not moves:
		return None
	if difficulty.allow_random:
		# 50% random on easy for variety
		if random.random() < 0.5:
			return random.choice(moves)
	value, move = minimax(state, depth=difficulty.depth, alpha=-math.inf, beta=math.inf, maximizing_player=state.to_move, use_alpha_beta=difficulty.use_alpha_beta)
	return move if move is not None else random.choice(moves)


def hint(state: GameState, difficulty: AIDifficulty = MEDIUM) -> Optional[Move]:
	return choose_move(state, difficulty)

