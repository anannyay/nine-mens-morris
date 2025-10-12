from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List

import pygame

from .constants import POINTS_NORM, PLAYER_WHITE, PLAYER_BLACK, EMPTY, ADJACENT
from .game_state import GameState, Move
from .ai import choose_move, EASY, MEDIUM, HARD, AIDifficulty, hint as ai_hint
from .stats import load_stats, save_stats, achievement_text, Stats
from .puzzles import load_puzzle, SAMPLE_PUZZLES


@dataclass
class UIConfig:
	width: int = 800
	height: int = 800
	margin: int = 60
	bg_color: Tuple[int, int, int] = (18, 18, 24)
	board_color: Tuple[int, int, int] = (200, 200, 200)
	white_color: Tuple[int, int, int] = (240, 240, 240)
	black_color: Tuple[int, int, int] = (20, 20, 20)
	highlight_color: Tuple[int, int, int] = (255, 215, 0)
	ghost_color: Tuple[int, int, int] = (100, 100, 120)
	text_color: Tuple[int, int, int] = (230, 230, 240)
	point_radius: int = 16
	selected_radius: int = 22
	anim_speed_px_per_s: float = 800.0


class UI:
	def __init__(self, state: GameState, ai_enabled: bool = False, ai_color: int = PLAYER_BLACK, difficulty: AIDifficulty = MEDIUM, config: Optional[UIConfig] = None) -> None:
		self.state = state
		self.ai_enabled = ai_enabled
		self.ai_color = ai_color
		self.difficulty = difficulty
		self.config = config or UIConfig()
		self._selected: Optional[int] = None
		self._anim: Optional[Tuple[int, int, float, float]] = None  # from_idx, to_idx, start_time, duration
		self._hint_move: Optional[Move] = None
		self._stats = load_stats()
		self._last_mill_count = 0
		self._dragging: bool = False
		self._drag_from: Optional[int] = None
		self._legal_targets: List[int] = []

		pygame.init()
		self.screen = pygame.display.set_mode((self.config.width, self.config.height))
		pygame.display.set_caption("Nine Men's Morris")
		self.clock = pygame.time.Clock()
		self.font = pygame.font.SysFont("Arial", 20)

	def norm_to_px(self, x: float, y: float) -> Tuple[int, int]:
		mx, my = self.config.margin, self.config.margin
		w = self.config.width - 2 * mx
		h = self.config.height - 2 * my
		return int(mx + x * w), int(my + y * h)

	def point_pos(self, idx: int) -> Tuple[int, int]:
		nx, ny = POINTS_NORM[idx]
		return self.norm_to_px(nx, ny)

	def nearest_point(self, pos: Tuple[int, int]) -> Optional[int]:
		x, y = pos
		for i in range(24):
			px, py = self.point_pos(i)
			if math.hypot(px - x, py - y) <= self.config.point_radius * 1.6:
				return i
		return None

	def draw_board(self) -> None:
		self.screen.fill(self.config.bg_color)
		c = self.config.board_color
		# Draw lines between adjacent points
		for i in range(24):
			for j in ADJACENT[i]:
				if j > i:
					pygame.draw.line(self.screen, c, self.point_pos(i), self.point_pos(j), 2)
		# Draw points and pieces
		for i in range(24):
			px, py = self.point_pos(i)
			pygame.draw.circle(self.screen, c, (px, py), self.config.point_radius, 2)
			v = self.state.board[i]
			if v != EMPTY:
				color = self.config.white_color if v == PLAYER_WHITE else self.config.black_color
				pygame.draw.circle(self.screen, color, (px, py), self.config.point_radius - 3)
			# highlight legal target
			if i in self._legal_targets:
				pygame.draw.circle(self.screen, self.config.highlight_color, (px, py), self.config.point_radius + 2, 2)
		# Draw selection highlight
		if self._selected is not None:
			px, py = self.point_pos(self._selected)
			pygame.draw.circle(self.screen, self.config.highlight_color, (px, py), self.config.selected_radius, 2)
		# Draw hint arrow
		if self._hint_move and self._hint_move.to_idx is not None:
			fx = self._hint_move.from_idx if self._hint_move.from_idx is not None else self._hint_move.to_idx
			if fx is not None:
				p1 = self.point_pos(fx)
				p2 = self.point_pos(self._hint_move.to_idx)
				pygame.draw.line(self.screen, self.config.highlight_color, p1, p2, 3)

		# Status text
		turn = "White" if self.state.to_move == PLAYER_WHITE else "Black"
		phase = self.state.phase + (" (remove)" if self.state.removal_pending else "")
		msg = f"Turn: {turn} | Phase: {phase} | W:{self.state.white_in_hand} B:{self.state.black_in_hand}"
		txt = self.font.render(msg, True, self.config.text_color)
		self.screen.blit(txt, (10, 10))
		ach_txt = achievement_text(self._stats)
		if ach_txt:
			badge = self.font.render(ach_txt, True, self.config.highlight_color)
			self.screen.blit(badge, (10, 36))

	def animate_move(self, from_idx: int, to_idx: int) -> None:
		p1 = self.point_pos(from_idx)
		p2 = self.point_pos(to_idx)
		distance = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
		dur = max(0.08, distance / self.config.anim_speed_px_per_s)
		self._anim = (from_idx, to_idx, time.time(), dur)

	def update_animation(self) -> None:
		if not self._anim:
			return
		from_idx, to_idx, start, dur = self._anim
		alpha = (time.time() - start) / dur
		if alpha >= 1.0:
			self._anim = None
			return
		# Draw moving ghost
		x1, y1 = self.point_pos(from_idx)
		x2, y2 = self.point_pos(to_idx)
		x = int(x1 + (x2 - x1) * alpha)
		y = int(y1 + (y2 - y1) * alpha)
		color = self.config.white_color if self.state.to_move == PLAYER_BLACK else self.config.black_color
		pygame.draw.circle(self.screen, self.config.ghost_color, (x, y), self.config.point_radius - 3)

	def handle_click(self, pos: Tuple[int, int]) -> None:
		if self.state.winner is not None:
			return
		idx = self.nearest_point(pos)
		if idx is None:
			self._selected = None
			return
		# Removal phase: choose opponent piece to remove
		if self.state.removal_pending:
			move = Move(player=self.state.to_move, remove_idx=idx)
			self._apply_and_record(move)
			self._selected = None
			return
		# Placing phase
		if self.state.phase == "placing":
			move = Move(player=self.state.to_move, to_idx=idx)
			if self._apply_and_record(move):
				self._selected = None
			return
		# Moving/flying
		if self._selected is None:
			if self.state.board[idx] == self.state.to_move:
				self._selected = idx
				self._compute_legal_targets(idx)
			return
		else:
			from_idx = self._selected
			move = Move(player=self.state.to_move, from_idx=from_idx, to_idx=idx)
			if self._apply_and_record(move):
				# Animate from -> to
				self.animate_move(from_idx, idx)
				self._selected = None
				self._legal_targets = []
				return
			# If failed, maybe reselect
			if self.state.board[idx] == self.state.to_move:
				self._selected = idx
				self._compute_legal_targets(idx)
			else:
				self._selected = None
				self._legal_targets = []

	def _compute_legal_targets(self, from_idx: int) -> None:
		self._legal_targets = []
		for mv in self.state.legal_moves():
			if mv.from_idx == from_idx:
				if mv.to_idx is not None:
					self._legal_targets.append(mv.to_idx)

	def _apply_and_record(self, move: Move) -> bool:
		before_to_move = self.state.to_move
		ok = self.state.apply_move(move)
		if not ok:
			return False
		# Stats via events
		for ev in self.state.events:
			if ev["type"] in ("placed", "moved"):
				self._stats.record_move()
			elif ev["type"] == "formed_mill":
				self._stats.record_mill()
				save_stats(self._stats)
			elif ev["type"] == "game_over":
				self._stats.record_win(ev["winner"])
				save_stats(self._stats)
		return True

	def maybe_ai_move(self) -> None:
		if not self.ai_enabled:
			return
		if self.state.winner is not None:
			return
		if self.state.to_move != self.ai_color:
			return
		mv = choose_move(self.state, self.difficulty)
		if mv:
			from_idx = mv.from_idx
			to_idx = mv.to_idx
			self._apply_and_record(mv)
			if from_idx is not None and to_idx is not None:
				self.animate_move(from_idx, to_idx)

	def set_difficulty(self, key: int) -> None:
		self.difficulty = {pygame.K_e: EASY, pygame.K_m: MEDIUM, pygame.K_h: HARD}.get(key, self.difficulty)

	def loop(self) -> None:
		running = True
		while running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					# Start drag if in moving/flying and clicked own piece; otherwise handle as click
					idx = self.nearest_point(event.pos)
					if idx is not None and self.state.phase != "placing" and not self.state.removal_pending and self.state.board[idx] == self.state.to_move:
						self._dragging = True
						self._drag_from = idx
						self._selected = idx
						self._compute_legal_targets(idx)
					else:
						self.handle_click(event.pos)
				elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._dragging:
					idx = self.nearest_point(event.pos)
					if idx is not None and self._drag_from is not None:
						mv = Move(player=self.state.to_move, from_idx=self._drag_from, to_idx=idx)
						if self._apply_and_record(mv):
							self.animate_move(self._drag_from, idx)
					self._selected = None
					self._legal_targets = []
					self._dragging = False
					self._drag_from = None
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_u:
						self.state.undo()
					elif event.key == pygame.K_r:
						self.state.redo()
					elif event.key in (pygame.K_e, pygame.K_m, pygame.K_h):
						self.set_difficulty(event.key)
					elif event.key == pygame.K_h:
						self._hint_move = ai_hint(self.state, self.difficulty)
					elif event.key == pygame.K_n:
						# new game
						self.state.reset()
						self._selected = None
						self._hint_move = None
						self._legal_targets = []
						self._dragging = False
						self._drag_from = None
					elif event.key == pygame.K_a:
						# toggle AI
						self.ai_enabled = not self.ai_enabled
					elif event.key == pygame.K_p:
						# load random puzzle
						from random import randint
						idx = randint(0, len(SAMPLE_PUZZLES) - 1)
						p = load_puzzle(idx)
						if p:
							self.state = p
							self._selected = None
							self._hint_move = None
							self._legal_targets = []
							self._dragging = False
							self._drag_from = None
			self.maybe_ai_move()
			self.draw_board()
			self.update_animation()
			if self.state.winner is not None:
				msg = "White wins!" if self.state.winner == PLAYER_WHITE else "Black wins!"
				banner = self.font.render(msg, True, self.config.highlight_color)
				rect = banner.get_rect(center=(self.config.width // 2, 30))
				self.screen.blit(banner, rect)
			pygame.display.flip()
			self.clock.tick(60)
		pygame.quit()

