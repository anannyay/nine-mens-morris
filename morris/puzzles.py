from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .constants import EMPTY, PLAYER_WHITE, PLAYER_BLACK
from .game_state import GameState


@dataclass
class Puzzle:
	name: str
	description: str
	board: List[int]  # length 24
	to_move: int
	white_in_hand: int = 0
	black_in_hand: int = 0


SAMPLE_PUZZLES: List[Puzzle] = [
	Puzzle(
		name="Win in 3 (sample)",
		description="White to move and force win in 3 moves.",
		board=[
			PLAYER_WHITE, EMPTY, PLAYER_WHITE,
			EMPTY, PLAYER_BLACK, EMPTY,
			PLAYER_BLACK, PLAYER_WHITE, EMPTY,
			EMPTY, EMPTY, PLAYER_BLACK,
			EMPTY, PLAYER_BLACK, EMPTY,
			EMPTY, PLAYER_WHITE, EMPTY,
			EMPTY, PLAYER_BLACK, EMPTY,
			EMPTY, EMPTY, EMPTY,
		],
		to_move=PLAYER_WHITE,
		white_in_hand=0,
		black_in_hand=0,
	),
	Puzzle(
		name="Clutch Defense",
		description="Black to move, avoid immediate loss.",
		board=[
			EMPTY, PLAYER_WHITE, PLAYER_WHITE,
			EMPTY, PLAYER_BLACK, EMPTY,
			EMPTY, PLAYER_WHITE, EMPTY,
			PLAYER_BLACK, EMPTY, EMPTY,
			EMPTY, EMPTY, PLAYER_BLACK,
			EMPTY, PLAYER_WHITE, EMPTY,
			EMPTY, EMPTY, EMPTY,
			PLAYER_BLACK, EMPTY, EMPTY,
		],
		to_move=PLAYER_BLACK,
		white_in_hand=0,
		black_in_hand=0,
	),
]


def load_puzzle(idx: int) -> Optional[GameState]:
	if idx < 0 or idx >= len(SAMPLE_PUZZLES):
		return None
	p = SAMPLE_PUZZLES[idx]
	state = GameState()
	state.board = p.board[:]
	state.to_move = p.to_move
	state.white_in_hand = p.white_in_hand
	state.black_in_hand = p.black_in_hand
	state.phase = "moving" if (p.white_in_hand == 0 and p.black_in_hand == 0) else "placing"
	state.removal_pending = False
	state.winner = None
	state.history.clear()
	state.redo_stack.clear()
	return state

