from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .constants import EMPTY, PLAYER_WHITE, PLAYER_BLACK, STARTING_STONES_PER_PLAYER, ADJACENT
from .rules import positions_in_mill, forms_mill, legal_removals


Phase = str  # "placing" | "moving" | "removing" (after mill) | "gameover"


@dataclass
class Move:
	# For placing: from_idx = None, to_idx set
	# For moving/flying: from_idx set, to_idx set
	# For removal (after mill): remove_idx set
	player: int
	from_idx: Optional[int] = None
	to_idx: Optional[int] = None
	remove_idx: Optional[int] = None


@dataclass
class GameState:
	board: List[int] = field(default_factory=lambda: [EMPTY] * 24)
	phase: Phase = "placing"
	to_move: int = PLAYER_WHITE
	white_in_hand: int = STARTING_STONES_PER_PLAYER
	black_in_hand: int = STARTING_STONES_PER_PLAYER
	removal_pending: bool = False
	winner: Optional[int] = None
	history: List[Tuple[List[int], Phase, int, int, int, bool, Optional[int]]] = field(default_factory=list)
	redo_stack: List[Tuple[List[int], Phase, int, int, int, bool, Optional[int]]] = field(default_factory=list)
	# Emitted events from the last successful apply_move call
	events: List[dict] = field(default_factory=list, init=False, repr=False)

	def clone(self) -> "GameState":
		copy = GameState()
		copy.board = self.board[:]
		copy.phase = self.phase
		copy.to_move = self.to_move
		copy.white_in_hand = self.white_in_hand
		copy.black_in_hand = self.black_in_hand
		copy.removal_pending = self.removal_pending
		copy.winner = self.winner
		# history/redo not copied intentionally for search performance
		copy.events = []
		return copy

	def reset(self) -> None:
		# Reinitialize to a fresh starting position
		self.__init__()

	def current_in_hand(self) -> int:
		return self.white_in_hand if self.to_move == PLAYER_WHITE else self.black_in_hand

	def set_current_in_hand(self, value: int) -> None:
		if self.to_move == PLAYER_WHITE:
			self.white_in_hand = value
		else:
			self.black_in_hand = value

	def num_pieces(self, player: int) -> int:
		return sum(1 for v in self.board if v == player)

	def is_flying(self, player: int) -> bool:
		return self.num_pieces(player) == 3 and self.phase != "placing"

	def push_history(self) -> None:
		self.history.append((self.board[:], self.phase, self.to_move, self.white_in_hand, self.black_in_hand, self.removal_pending, self.winner))
		self.redo_stack.clear()

	def undo(self) -> bool:
		if not self.history:
			return False
		self.redo_stack.append((self.board[:], self.phase, self.to_move, self.white_in_hand, self.black_in_hand, self.removal_pending, self.winner))
		prev = self.history.pop()
		(self.board, self.phase, self.to_move, self.white_in_hand, self.black_in_hand, self.removal_pending, self.winner) = prev
		return True

	def redo(self) -> bool:
		if not self.redo_stack:
			return False
		self.history.append((self.board[:], self.phase, self.to_move, self.white_in_hand, self.black_in_hand, self.removal_pending, self.winner))
		next_state = self.redo_stack.pop()
		(self.board, self.phase, self.to_move, self.white_in_hand, self.black_in_hand, self.removal_pending, self.winner) = next_state
		return True

	def legal_moves(self) -> List[Move]:
		if self.winner is not None:
			return []
		if self.removal_pending:
			# Removal selection moves only
			opponent = PLAYER_WHITE if self.to_move == PLAYER_BLACK else PLAYER_BLACK
			return [Move(player=self.to_move, remove_idx=i) for i in legal_removals(self.board, opponent)]
		if self.phase == "placing":
			return [Move(player=self.to_move, to_idx=i) for i, v in enumerate(self.board) if v == EMPTY]
		# moving or flying
		moves: List[Move] = []
		flying = self.is_flying(self.to_move)
		for i, v in enumerate(self.board):
			if v != self.to_move:
				continue
			if flying:
				for j, val in enumerate(self.board):
					if val == EMPTY:
						moves.append(Move(player=self.to_move, from_idx=i, to_idx=j))
			else:
				for j in ADJACENT[i]:
					if self.board[j] == EMPTY:
						moves.append(Move(player=self.to_move, from_idx=i, to_idx=j))
		return moves

	def apply_move(self, move: Move) -> bool:
		if self.winner is not None:
			return False
		self.events = []
		prev_phase = self.phase
		self.push_history()
		if move.remove_idx is not None and self.removal_pending:
			if self.board[move.remove_idx] in (EMPTY, self.to_move):
				self.history.pop()  # revert push
				return False
			self.board[move.remove_idx] = EMPTY
			self.removal_pending = False
			self.events.append({"type": "removed", "player": self.to_move, "idx": move.remove_idx})
			# Switch turn after removal finishes
			self.to_move *= -1
			self._update_phase_and_winner()
			if self.phase != prev_phase:
				self.events.append({"type": "phase_change", "from": prev_phase, "to": self.phase})
			if self.winner is not None:
				self.events.append({"type": "game_over", "winner": self.winner})
			return True
		if self.phase == "placing":
			if move.to_idx is None or self.board[move.to_idx] != EMPTY:
				self.history.pop()
				return False
			self.board[move.to_idx] = self.to_move
			self.set_current_in_hand(self.current_in_hand() - 1)
			self.events.append({"type": "placed", "player": self.to_move, "to": move.to_idx})
			# Check mill
			if forms_mill(self.board, move.to_idx, self.to_move):
				self.removal_pending = True
				self.events.append({"type": "formed_mill", "player": self.to_move, "at": move.to_idx})
				return True
			# No mill -> switch turn
			self.to_move *= -1
			self._update_phase_and_winner()
			if self.phase != prev_phase:
				self.events.append({"type": "phase_change", "from": prev_phase, "to": self.phase})
			if self.winner is not None:
				self.events.append({"type": "game_over", "winner": self.winner})
			return True
		# moving or flying
		if move.from_idx is None or move.to_idx is None:
			self.history.pop()
			return False
		if self.board[move.from_idx] != self.to_move or self.board[move.to_idx] != EMPTY:
			self.history.pop()
			return False
		if not self.is_flying(self.to_move) and move.to_idx not in ADJACENT[move.from_idx]:
			self.history.pop()
			return False
		self.board[move.from_idx] = EMPTY
		self.board[move.to_idx] = self.to_move
		self.events.append({"type": "moved", "player": self.to_move, "from": move.from_idx, "to": move.to_idx})
		if forms_mill(self.board, move.to_idx, self.to_move):
			self.removal_pending = True
			self.events.append({"type": "formed_mill", "player": self.to_move, "at": move.to_idx})
			return True
		self.to_move *= -1
		self._update_phase_and_winner()
		if self.phase != prev_phase:
			self.events.append({"type": "phase_change", "from": prev_phase, "to": self.phase})
		if self.winner is not None:
			self.events.append({"type": "game_over", "winner": self.winner})
		return True

	def _update_phase_and_winner(self) -> None:
		if self.white_in_hand == 0 and self.black_in_hand == 0 and self.phase == "placing" and not self.removal_pending:
			self.phase = "moving"
		if self.winner is None and not self.removal_pending:
			self.winner = self._check_winner()

	def _check_winner(self) -> Optional[int]:
		# Opponent loses if less than 3 pieces or no legal moves when not placing
		for player in (PLAYER_WHITE, PLAYER_BLACK):
			pieces = self.num_pieces(player)
			if pieces < 3 and (self.white_in_hand == 0 if player == PLAYER_WHITE else self.black_in_hand == 0):
				return -player
		# Stalemate: current player cannot move (not in placing and not removal)
		if self.phase != "placing" and not self.removal_pending:
			if not self.legal_moves():
				return -self.to_move
		return None

