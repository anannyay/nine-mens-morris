from __future__ import annotations

import argparse

from morris.game_state import GameState
from morris.ui import UI
from morris.constants import PLAYER_WHITE, PLAYER_BLACK
from morris.ai import EASY, MEDIUM, HARD


def parse_args():
	parser = argparse.ArgumentParser(description="Nine Men's Morris")
	parser.add_argument("--ai", action="store_true", help="Enable AI opponent")
	parser.add_argument("--ai-color", choices=["white", "black"], default="black")
	parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
	return parser.parse_args()


def main():
	args = parse_args()
	state = GameState()
	ai_enabled = args.ai
	ai_color = PLAYER_WHITE if args.ai_color == "white" else PLAYER_BLACK
	level = {"easy": EASY, "medium": MEDIUM, "hard": HARD}[args.difficulty]
	ui = UI(state, ai_enabled=ai_enabled, ai_color=ai_color, difficulty=level)
	ui.loop()


if __name__ == "__main__":
	main()