from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict

from .constants import PLAYER_WHITE, PLAYER_BLACK


DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".morris_stats.json")


@dataclass
class Stats:
	white_wins: int = 0
	black_wins: int = 0
	mills_formed: int = 0
	total_games: int = 0
	total_moves: int = 0

	def record_win(self, winner: int) -> None:
		if winner == PLAYER_WHITE:
			self.white_wins += 1
		elif winner == PLAYER_BLACK:
			self.black_wins += 1
		self.total_games += 1

	def record_move(self) -> None:
		self.total_moves += 1

	def record_mill(self) -> None:
		self.mills_formed += 1

	def average_moves_per_game(self) -> float:
		return (self.total_moves / self.total_games) if self.total_games else 0.0


def load_stats(path: str = DEFAULT_PATH) -> Stats:
	if not os.path.exists(path):
		return Stats()
	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return Stats(**data)
	except Exception:
		return Stats()


def save_stats(stats: Stats, path: str = DEFAULT_PATH) -> None:
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(asdict(stats), f)
	except Exception:
		pass


def achievement_text(stats: Stats) -> str:
	msgs = []
	if stats.mills_formed >= 10:
		msgs.append("Mill Master!")
	if stats.total_games >= 5:
		msgs.append("Veteran!")
	if stats.average_moves_per_game() <= 20 and stats.total_games >= 3:
		msgs.append("Speedster!")
	return " ".join(msgs)

