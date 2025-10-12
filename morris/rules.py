from __future__ import annotations

from typing import Iterable, List, Optional

from .constants import MILLS, ADJACENT, EMPTY, PLAYER_WHITE, PLAYER_BLACK


def positions_in_mill(board: List[int], idx: int) -> Optional[List[int]]:
	"""Return the mill triplet if idx is part of a formed mill for its occupant; else None."""
	player = board[idx]
	if player == EMPTY:
		return None
	for a, b, c in MILLS:
		if idx in (a, b, c) and board[a] == board[b] == board[c] == player:
			return [a, b, c]
	return None


def forms_mill(board: List[int], idx: int, player: int) -> bool:
	"""Check if placing/moving player at idx forms a mill."""
	for a, b, c in MILLS:
		if idx in (a, b, c):
			line = [a, b, c]
			if all((board[p] == player if p != idx else True) for p in line):
				# ensure all 3 equal to player, with idx being player's after move
				if all(board[p] == player for p in line if p != idx):
					return True
	return False


def legal_removals(board: List[int], opponent: int) -> List[int]:
	"""Return indices of opponent pieces that can be removed given a mill formed.

	Prefer removing pieces not in mills; only if all are in mills, allow removing any.
	"""
	opponent_positions = [i for i, v in enumerate(board) if v == opponent]
	if not opponent_positions:
		return []
	not_in_mill = [i for i in opponent_positions if positions_in_mill(board, i) is None]
	return not_in_mill if not_in_mill else opponent_positions


def neighbors_of(idx: int) -> List[int]:
	return ADJACENT[idx][:]

