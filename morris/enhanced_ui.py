from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List

import pygame

from .constants import POINTS_NORM, PLAYER_WHITE, PLAYER_BLACK, EMPTY, ADJACENT, MILLS
from .game_state import GameState, Move
from .ai import choose_move, EASY, MEDIUM, HARD, AIDifficulty, hint as ai_hint
from .stats import load_stats, save_stats, achievement_text, Stats
from .puzzles import load_puzzle, SAMPLE_PUZZLES


@dataclass
class UIConfig:
	width: int = 1200
	height: int = 800
	margin: int = 60
	bg_color: Tuple[int, int, int] = (15, 15, 25)
	board_color: Tuple[int, int, int] = (180, 180, 190)
	white_color: Tuple[int, int, int] = (255, 255, 255)  # Pure white for better contrast
	black_color: Tuple[int, int, int] = (20, 20, 20)     # Pure black for better contrast
	highlight_color: Tuple[int, int, int] = (100, 200, 255)
	accent_color: Tuple[int, int, int] = (80, 150, 220)
	ghost_color: Tuple[int, int, int] = (100, 100, 120)
	text_color: Tuple[int, int, int] = (230, 230, 240)
	card_bg: Tuple[int, int, int] = (28, 28, 38)
	card_border: Tuple[int, int, int] = (60, 60, 80)
	point_radius: int = 16
	selected_radius: int = 22
	anim_speed_px_per_s: float = 800.0
	board_offset_x: int = 80  # Offset to center board with sidebar
	light_mode: bool = False  # Theme toggle


@dataclass
class LightTheme:
	bg_color: Tuple[int, int, int] = (248, 248, 252)
	board_color: Tuple[int, int, int] = (60, 60, 70)
	white_color: Tuple[int, int, int] = (255, 255, 255)  # Pure white for better contrast
	black_color: Tuple[int, int, int] = (20, 20, 20)    # Pure black for better contrast
	highlight_color: Tuple[int, int, int] = (0, 100, 200)
	accent_color: Tuple[int, int, int] = (0, 80, 160)
	ghost_color: Tuple[int, int, int] = (120, 120, 140)
	text_color: Tuple[int, int, int] = (30, 30, 40)
	card_bg: Tuple[int, int, int] = (255, 255, 255)
	card_border: Tuple[int, int, int] = (200, 200, 210)


class Screen:
	WELCOME = "welcome"
	RULES = "rules"
	AI_EXPLANATION = "ai_explanation"
	GAME = "game"


class Card:
	"""Interactive card for tutorial/explanation screens"""
	def __init__(self, x: int, y: int, width: int, height: int, title: str, content: List[str], 
	             config: UIConfig, icon: Optional[str] = None):
		self.rect = pygame.Rect(x, y, width, height)
		self.title = title
		self.content = content
		self.config = config
		self.icon = icon
		self.hovered = False
	
	def contains(self, pos: Tuple[int, int]) -> bool:
		return self.rect.collidepoint(pos)
	
	def draw(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font, theme_colors) -> None:
		# Card background with subtle border
		border_width = 3 if self.hovered else 1
		pygame.draw.rect(screen, theme_colors.card_border, self.rect, border_radius=12)
		inner_rect = self.rect.inflate(-border_width*2, -border_width*2)
		pygame.draw.rect(screen, theme_colors.card_bg, inner_rect, border_radius=10)
		
		# Title
		title_surf = font.render(self.title, True, theme_colors.highlight_color)
		title_rect = title_surf.get_rect(centerx=self.rect.centerx, top=self.rect.top + 20)
		screen.blit(title_surf, title_rect)
		
		# Content with text wrapping
		y_offset = title_rect.bottom + 20
		line_height = 24
		text_margin = 20
		max_width = self.rect.width - 2 * text_margin
		
		for line in self.content:
			# Handle text wrapping for long lines
			words = line.split()
			current_line = ""
			
			for word in words:
				test_line = current_line + (" " if current_line else "") + word
				text_width = small_font.size(test_line)[0]
				
				if text_width <= max_width:
					current_line = test_line
				else:
					# Render current line if it has content
					if current_line:
						text_surf = small_font.render(current_line, True, theme_colors.text_color)
						text_rect = text_surf.get_rect(left=self.rect.left + text_margin, top=y_offset)
						screen.blit(text_surf, text_rect)
						y_offset += line_height
					current_line = word
			
			# Render the last line
			if current_line:
				text_surf = small_font.render(current_line, True, theme_colors.text_color)
				text_rect = text_surf.get_rect(left=self.rect.left + text_margin, top=y_offset)
				screen.blit(text_surf, text_rect)
				y_offset += line_height


class Button:
	"""Modern button with hover effects"""
	def __init__(self, x: int, y: int, width: int, height: int, text: str, config: UIConfig):
		self.rect = pygame.Rect(x, y, width, height)
		self.text = text
		self.config = config
		self.hovered = False
		self.clicked = False
	
	def contains(self, pos: Tuple[int, int]) -> bool:
		return self.rect.collidepoint(pos)
	
	def draw(self, screen: pygame.Surface, font: pygame.font.Font, theme_colors) -> None:
		color = theme_colors.highlight_color if self.hovered else theme_colors.accent_color
		pygame.draw.rect(screen, color, self.rect, border_radius=8)
		text_color = theme_colors.bg_color if self.hovered else theme_colors.text_color
		text_surf = font.render(self.text, True, text_color)
		text_rect = text_surf.get_rect(center=self.rect.center)
		screen.blit(text_surf, text_rect)


class EnhancedUI:
	def __init__(self, state: GameState, ai_enabled: bool = False, ai_color: int = PLAYER_BLACK, 
	             difficulty: AIDifficulty = MEDIUM, config: Optional[UIConfig] = None) -> None:
		self.state = state
		self.ai_enabled = ai_enabled
		self.ai_color = ai_color
		self.difficulty = difficulty
		self.config = config or UIConfig()
		self.light_theme = LightTheme()
		self._selected: Optional[int] = None
		self._anim: Optional[Tuple[int, int, float, float]] = None
		self._hint_move: Optional[Move] = None
		self._stats = load_stats()
		self._dragging: bool = False
		self._drag_from: Optional[int] = None
		self._legal_targets: List[int] = []
		
		# Screen management
		self.current_screen = Screen.WELCOME
		self.cards: List[Card] = []
		self.buttons: List[Button] = []
		
		pygame.init()
		self.screen = pygame.display.set_mode((self.config.width, self.config.height))
		pygame.display.set_caption("Nine Men's Morris - Strategic Board Game")
		self.clock = pygame.time.Clock()
		self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
		self.font = pygame.font.SysFont("Arial", 22)
		self.font_small = pygame.font.SysFont("Arial", 18)
		self.font_tiny = pygame.font.SysFont("Arial", 14)
		
		# Overlays
		self._show_ai_overlay = False
		
		self._setup_welcome_screen()
	
	def _get_theme_colors(self):
		"""Get current theme colors based on light_mode setting"""
		if self.config.light_mode:
			return self.light_theme
		return self.config
	
	def _toggle_theme(self):
		"""Toggle between dark and light mode"""
		self.config.light_mode = not self.config.light_mode
		# Refresh the current screen
		if self.current_screen == Screen.WELCOME:
			self._setup_welcome_screen()
		elif self.current_screen == Screen.RULES:
			self._setup_rules_screen()
		elif self.current_screen == Screen.AI_EXPLANATION:
			self._setup_ai_screen()
	
	def _setup_welcome_screen(self) -> None:
		"""Setup welcome screen with intro cards"""
		self.cards = []
		self.buttons = []
		
		# Title
		w, h = self.config.width, self.config.height
		
		# Cards explaining the game
		card_width = 340
		card_height = 280
		spacing = 20
		start_x = (w - (card_width * 3 + spacing * 2)) // 2
		start_y = 150
		
		# Card 1: Objective
		self.cards.append(Card(
			start_x, start_y, card_width, card_height,
			"Game Objective",
			[
				"• Form mills (3 in a row)",
				"• Capture opponent's pieces",
				"• Reduce opponent to < 3 pieces",
				"",
				"Win by:",
				"• Capturing pieces",
				"• Blocking all moves"
			],
			self.config,
			"objective"
		))
		
		# Card 2: Game Phases
		self.cards.append(Card(
			start_x + card_width + spacing, start_y, card_width, card_height,
			"Three Phases",
			[
				"1. PLACING (9 pieces each)",
				"   Place pieces on empty spots",
				"",
				"2. MOVING",
				"   Slide to adjacent spots",
				"",
				"3. FLYING (3 pieces left)",
				"   Jump to any empty spot"
			],
			self.config,
			"phases"
		))
		
		# Card 3: Mill Formation
		self.cards.append(Card(
			start_x + (card_width + spacing) * 2, start_y, card_width, card_height,
			"Mills & Capturing",
			[
				"• Form a mill (3 in a row)",
				"• Remove 1 opponent piece",
				"• Can't remove from mills",
				"  (unless all in mills)",
				"",
				"Break & reform mills to",
				"capture multiple times!"
			],
			self.config,
			"mill"
		))
		
		# Buttons with better layout
		btn_width = 200
		btn_height = 55
		btn_spacing = 20
		total_btn_width = btn_width * 4 + btn_spacing * 3
		btn_start_x = (w - total_btn_width) // 2
		btn_y = start_y + card_height + 50
		
		# Main action buttons
		self.buttons.append(Button(btn_start_x, btn_y, btn_width, btn_height, "🎮 Start Game", self.config))
		self.buttons.append(Button(btn_start_x + btn_width + btn_spacing, btn_y, btn_width, btn_height, "🤖 Learn AI", self.config))
		self.buttons.append(Button(btn_start_x + (btn_width + btn_spacing) * 2, btn_y, btn_width, btn_height, "📖 View Rules", self.config))
		self.buttons.append(Button(btn_start_x + (btn_width + btn_spacing) * 3, btn_y, btn_width, btn_height, "❌ Exit Game", self.config))
		
		# AI status indicator
		ai_status_y = btn_y + btn_height + 30
		ai_status_text = f"🤖 AI: {'ON' if self.ai_enabled else 'OFF'} ({self.difficulty.name})"
		ai_status_rect = pygame.Rect(btn_start_x, ai_status_y, total_btn_width, 40)
		ai_status_button = Button(ai_status_rect.x, ai_status_rect.y, ai_status_rect.width, ai_status_rect.height, ai_status_text, self.config)
		self.buttons.append(ai_status_button)
	
	def _setup_rules_screen(self) -> None:
		"""Setup detailed rules screen"""
		self.cards = []
		self.buttons = []
		
		w, h = self.config.width, self.config.height
		card_width = 500
		card_height = 220
		spacing = 20
		start_x = (w - (card_width * 2 + spacing)) // 2
		start_y = 100
		
		# Detailed rules cards
		self.cards.append(Card(
			start_x, start_y, card_width, card_height,
			"Setup & Placing Phase",
			[
				"• Board has 24 positions in 3 squares",
				"• Each player has 9 pieces",
				"• White moves first",
				"• Take turns placing pieces",
				"• Form mills to capture pieces",
				"• Phase ends when all placed"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x + card_width + spacing, start_y, card_width, card_height,
			"Moving Phase",
			[
				"• Slide pieces to adjacent spots",
				"• Only along board lines",
				"• Cannot jump over pieces",
				"• Form mills to capture",
				"• Strategic positioning key",
				"• Continue until 3 pieces left"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x, start_y + card_height + spacing, card_width, card_height,
			"Flying Phase",
			[
				"• Activates with 3 pieces left",
				"• Jump to ANY empty position",
				"• Powerful mobility advantage",
				"• Still form mills to capture",
				"• Often decisive phase"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x + card_width + spacing, start_y + card_height + spacing, card_width, card_height,
			"Strategy Tips",
			[
				"• Control center positions",
				"• Build potential mills",
				"• Break & reform mills",
				"• Block opponent moves",
				"• Plan 2-3 moves ahead"
			],
			self.config
		))
		
		# Back button
		btn_width = 200
		btn_height = 50
		btn_x = (w - btn_width) // 2
		btn_y = start_y + card_height * 2 + spacing * 2 + 20
		self.buttons.append(Button(btn_x, btn_y, btn_width, btn_height, "Back", self.config))
	
	def _setup_ai_screen(self) -> None:
		"""Setup AI explanation screen"""
		self.cards = []
		self.buttons = []
		
		w, h = self.config.width, self.config.height
		card_width = 520
		card_height = 240
		spacing = 20
		start_x = (w - (card_width * 2 + spacing)) // 2
		start_y = 80
		
		# AI Algorithm cards
		self.cards.append(Card(
			start_x, start_y, card_width, card_height,
			"Minimax Algorithm",
			[
				"• Searches future game states",
				"• Assumes optimal opponent play",
				"• Evaluates positions recursively",
				"• Maximizes AI advantage",
				"• Minimizes your advantage",
				"",
				"Depth = moves ahead to analyze"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x + card_width + spacing, start_y, card_width, card_height,
			"Alpha-Beta Pruning",
			[
				"• Optimization technique",
				"• Skips irrelevant branches",
				"• Same result, faster search",
				"• Enables deeper analysis",
				"• Used in Medium/Hard modes",
				"",
				"Can search 10x faster!"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x, start_y + card_height + spacing, card_width, card_height,
			"Position Evaluation",
			[
				"Heuristic function considers:",
				"• Piece count difference (×100)",
				"• Mobility (legal moves) (×2)",
				"• Pieces on board vs hand",
				"• Win/loss states (±10,000)",
				"",
				"Balances material & strategy"
			],
			self.config
		))
		
		self.cards.append(Card(
			start_x + card_width + spacing, start_y + card_height + spacing, card_width, card_height,
			"Difficulty Levels",
			[
				"EASY: Depth 1, 50% random",
				"  Fast, makes mistakes",
				"",
				"MEDIUM: Depth 3, alpha-beta",
				"  Solid tactical play",
				"",
				"HARD: Depth 5, alpha-beta",
				"  Strong strategic planning"
			],
			self.config
		))
		
		# Back button
		btn_width = 200
		btn_height = 50
		btn_x = (w - btn_width) // 2
		btn_y = start_y + card_height * 2 + spacing * 2 + 20
		self.buttons.append(Button(btn_x, btn_y, btn_width, btn_height, "Back", self.config))
	
	def _draw_welcome_screen(self) -> None:
		"""Draw welcome screen"""
		theme = self._get_theme_colors()
		self.screen.fill(theme.bg_color)
		
		# Title
		title = self.font_large.render("Nine Men's Morris", True, theme.highlight_color)
		subtitle = self.font.render("Strategic Board Game with AI", True, theme.text_color)
		title_rect = title.get_rect(center=(self.config.width // 2, 60))
		subtitle_rect = subtitle.get_rect(center=(self.config.width // 2, 100))
		self.screen.blit(title, title_rect)
		self.screen.blit(subtitle, subtitle_rect)
		
		# Draw cards
		for card in self.cards:
			card.draw(self.screen, self.font, self.font_small, theme)
		
		# Draw buttons
		for button in self.buttons:
			button.draw(self.screen, self.font, theme)
		
		# Footer with theme toggle info
		footer_text = "Press ESC to return to welcome screen anytime | Press T to toggle theme"
		footer = self.font_tiny.render(footer_text, True, theme.text_color)
		footer_rect = footer.get_rect(center=(self.config.width // 2, self.config.height - 20))
		self.screen.blit(footer, footer_rect)
	
	def _draw_rules_screen(self) -> None:
		"""Draw rules screen"""
		theme = self._get_theme_colors()
		self.screen.fill(theme.bg_color)
		
		# Title
		title = self.font_large.render("Game Rules & Strategy", True, theme.highlight_color)
		title_rect = title.get_rect(center=(self.config.width // 2, 40))
		self.screen.blit(title, title_rect)
		
		# Draw cards
		for card in self.cards:
			card.draw(self.screen, self.font, self.font_small, theme)
		
		# Draw buttons
		for button in self.buttons:
			button.draw(self.screen, self.font, theme)
	
	def _draw_ai_screen(self) -> None:
		"""Draw AI explanation screen"""
		theme = self._get_theme_colors()
		self.screen.fill(theme.bg_color)
		
		# Title
		title = self.font_large.render("How the AI Works", True, theme.highlight_color)
		title_rect = title.get_rect(center=(self.config.width // 2, 35))
		self.screen.blit(title, title_rect)
		
		# Draw cards
		for card in self.cards:
			card.draw(self.screen, self.font, self.font_small, theme)
		
		# Draw buttons
		for button in self.buttons:
			button.draw(self.screen, self.font, theme)
	
	def norm_to_px(self, x: float, y: float) -> Tuple[int, int]:
		mx = self.config.margin + self.config.board_offset_x
		my = self.config.margin
		board_size = min(self.config.width - 2 * mx - 250, self.config.height - 2 * my)
		return int(mx + x * board_size), int(my + y * board_size)
	
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
	
	def _draw_mill_indicators(self) -> None:
		"""Highlight mills on the board with better visual effects"""
		theme = self._get_theme_colors()
		for mill in MILLS:
			a, b, c = mill
			if self.state.board[a] == self.state.board[b] == self.state.board[c] != EMPTY:
				# This is an active mill - draw connecting lines
				player = self.state.board[a]
				mill_color = (100, 255, 100) if player == PLAYER_WHITE else (255, 100, 100)
				
				# Draw lines connecting the mill
				points = [self.point_pos(idx) for idx in mill]
				pygame.draw.lines(self.screen, mill_color, False, points, 4)
				
				# Add glow effect
				for idx in mill:
					px, py = self.point_pos(idx)
					# Outer glow
					pygame.draw.circle(self.screen, mill_color, (px, py), self.config.point_radius + 6, 3)
					# Inner highlight
					pygame.draw.circle(self.screen, mill_color, (px, py), self.config.point_radius + 2, 2)

	def _draw_wrapped(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int], x: int, y: int, max_width: int) -> int:
		"""Draw wrapped text at x,y within max_width. Returns next y after the block."""
		words = text.split()
		line = ""
		line_height = font.get_linesize()
		for word in words:
			test = (line + (" " if line else "") + word)
			if font.size(test)[0] <= max_width:
				line = test
			else:
				if line:
					surf = font.render(line, True, color)
					self.screen.blit(surf, (x, y))
					y += line_height
				line = word
		if line:
			surf = font.render(line, True, color)
			self.screen.blit(surf, (x, y))
			y += line_height
		return y
	
	def _draw_sidebar(self) -> None:
		"""Draw game info sidebar"""
		theme = self._get_theme_colors()
		sidebar_x = self.config.width - 320
		sidebar_y = 20
		sidebar_width = 300
		
		# Game info panel
		panel_rect = pygame.Rect(sidebar_x, sidebar_y, sidebar_width, 180)
		pygame.draw.rect(self.screen, theme.card_bg, panel_rect, border_radius=10)
		pygame.draw.rect(self.screen, theme.card_border, panel_rect, 2, border_radius=10)
		
		y_offset = sidebar_y + 15
		
		# Current turn with removal indicator
		turn_text = "White's Turn" if self.state.to_move == PLAYER_WHITE else "Black's Turn"
		if self.state.removal_pending:
			turn_text += " (REMOVE PIECE!)"
		turn_surf = self.font.render(turn_text, True, theme.highlight_color)
		self.screen.blit(turn_surf, (sidebar_x + 15, y_offset))
		y_offset += 35
		
		# Phase with better indicators
		phase_text = f"Phase: {self.state.phase.title()}"
		if self.state.removal_pending:
			phase_text = "⚠️ REMOVAL PHASE ⚠️"
		phase_surf = self.font_small.render(phase_text, True, theme.highlight_color if self.state.removal_pending else theme.text_color)
		self.screen.blit(phase_surf, (sidebar_x + 15, y_offset))
		y_offset += 30
		
		# Pieces in hand
		white_hand = f"White pieces: {self.state.white_in_hand}"
		black_hand = f"Black pieces: {self.state.black_in_hand}"
		white_surf = self.font_small.render(white_hand, True, theme.text_color)
		black_surf = self.font_small.render(black_hand, True, theme.text_color)
		self.screen.blit(white_surf, (sidebar_x + 15, y_offset))
		y_offset += 25
		self.screen.blit(black_surf, (sidebar_x + 15, y_offset))
		y_offset += 30
		
		# On board
		white_on_board = self.state.num_pieces(PLAYER_WHITE)
		black_on_board = self.state.num_pieces(PLAYER_BLACK)
		board_text = f"On board: W:{white_on_board} B:{black_on_board}"
		board_surf = self.font_small.render(board_text, True, theme.text_color)
		self.screen.blit(board_surf, (sidebar_x + 15, y_offset))
		
		# Controls panel
		y_offset = sidebar_y + 200
		controls_rect = pygame.Rect(sidebar_x, y_offset, sidebar_width, 320)
		pygame.draw.rect(self.screen, theme.card_bg, controls_rect, border_radius=10)
		pygame.draw.rect(self.screen, theme.card_border, controls_rect, 2, border_radius=10)
		
		y_offset += 15
		controls_title = self.font.render("Controls", True, theme.highlight_color)
		self.screen.blit(controls_title, (sidebar_x + 15, y_offset))
		y_offset += 35
		
		controls = [
			("H", "Show hint"),
			("U", "Undo move"),
			("R", "Redo move"),
			("N", "New game"),
			("A", "Toggle AI"),
			("E/M/H", "Difficulty"),
			("P", "Load puzzle"),
			("I", "Toggle AI details"),
			("T", "Toggle theme"),
			("Q", "Quit game"),
			("ESC", "Welcome screen")
		]
		
		for key, desc in controls:
			key_surf = self.font_small.render(f"{key}:", True, theme.accent_color)
			desc_surf = self.font_small.render(desc, True, theme.text_color)
			self.screen.blit(key_surf, (sidebar_x + 15, y_offset))
			self.screen.blit(desc_surf, (sidebar_x + 80, y_offset))
			y_offset += 28
		
		# AI details overlay (toggle with I)
		if self._show_ai_overlay:
			overlay_y = y_offset + 10
			overlay_rect = pygame.Rect(sidebar_x, overlay_y, sidebar_width, 180)
			pygame.draw.rect(self.screen, theme.card_bg, overlay_rect, border_radius=10)
			pygame.draw.rect(self.screen, theme.card_border, overlay_rect, 2, border_radius=10)
			
			title = self.font.render("AI Details", True, theme.highlight_color)
			self.screen.blit(title, (sidebar_x + 15, overlay_y + 12))
			
			# Key-values with wrapping
			depth_map = {"Easy": 1, "Medium": 3, "Hard": 5}
			alpha_beta_map = {"Easy": False, "Medium": True, "Hard": True}
			random_map = {"Easy": "50%", "Medium": "0%", "Hard": "0%"}
			kv = [
				f"Mode: {self.difficulty.name}",
				f"Search depth: {depth_map.get(self.difficulty.name, 3)}",
				f"Alpha-beta: {'Yes' if alpha_beta_map.get(self.difficulty.name, True) else 'No'}",
				f"Randomness: {random_map.get(self.difficulty.name, '0%')}",
				"Heuristic: material, mobility, phase, win/loss"
			]
			ly = overlay_y + 48
			max_w = sidebar_width - 30
			for line in kv:
				ly = self._draw_wrapped(line, self.font_small, theme.text_color, sidebar_x + 15, ly, max_w)
		
		# AI status
		y_offset = sidebar_y + 540
		ai_rect = pygame.Rect(sidebar_x, y_offset, sidebar_width, 100)
		pygame.draw.rect(self.screen, theme.card_bg, ai_rect, border_radius=10)
		pygame.draw.rect(self.screen, theme.card_border, ai_rect, 2, border_radius=10)
		
		y_offset += 15
		ai_status = "AI: ON" if self.ai_enabled else "AI: OFF"
		ai_color = "White" if self.ai_color == PLAYER_WHITE else "Black"
		ai_text = f"{ai_status} ({ai_color})"
		ai_surf = self.font_small.render(ai_text, True, theme.highlight_color)
		self.screen.blit(ai_surf, (sidebar_x + 15, y_offset))
		y_offset += 30
		
		diff_text = f"Difficulty: {self.difficulty.name}"
		diff_surf = self.font_small.render(diff_text, True, theme.text_color)
		self.screen.blit(diff_surf, (sidebar_x + 15, y_offset))
		
		# Achievement badge
		ach = achievement_text(self._stats)
		if ach:
			y_offset += 30
			ach_surf = self.font_small.render(ach, True, theme.highlight_color)
			self.screen.blit(ach_surf, (sidebar_x + 15, y_offset))
	
	def draw_board(self) -> None:
		"""Draw game board"""
		theme = self._get_theme_colors()
		self.screen.fill(theme.bg_color)
		
		c = theme.board_color
		# Draw lines between adjacent points
		for i in range(24):
			for j in ADJACENT[i]:
				if j > i:
					pygame.draw.line(self.screen, c, self.point_pos(i), self.point_pos(j), 2)
		
		# Draw mill indicators
		self._draw_mill_indicators()
		
		# Draw points and pieces
		for i in range(24):
			px, py = self.point_pos(i)
			pygame.draw.circle(self.screen, c, (px, py), self.config.point_radius, 2)
			v = self.state.board[i]
			if v != EMPTY:
				color = theme.white_color if v == PLAYER_WHITE else theme.black_color
				# Draw piece with border for better visibility
				pygame.draw.circle(self.screen, color, (px, py), self.config.point_radius - 3)
				# Add contrasting border
				border_color = theme.black_color if v == PLAYER_WHITE else theme.white_color
				pygame.draw.circle(self.screen, border_color, (px, py), self.config.point_radius - 3, 2)
			# highlight legal target
			if i in self._legal_targets:
				pygame.draw.circle(self.screen, theme.highlight_color, (px, py), self.config.point_radius + 2, 2)
		
		# Draw selection highlight
		if self._selected is not None:
			px, py = self.point_pos(self._selected)
			pygame.draw.circle(self.screen, theme.highlight_color, (px, py), self.config.selected_radius, 3)
		
		# Draw hint arrow
		if self._hint_move and self._hint_move.to_idx is not None:
			fx = self._hint_move.from_idx if self._hint_move.from_idx is not None else self._hint_move.to_idx
			if fx is not None:
				p1 = self.point_pos(fx)
				p2 = self.point_pos(self._hint_move.to_idx)
				pygame.draw.line(self.screen, self.config.highlight_color, p1, p2, 4)
				# Draw arrow head
				angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
				arrow_size = 15
				pygame.draw.polygon(self.screen, self.config.highlight_color, [
					p2,
					(p2[0] - arrow_size * math.cos(angle - math.pi/6), p2[1] - arrow_size * math.sin(angle - math.pi/6)),
					(p2[0] - arrow_size * math.cos(angle + math.pi/6), p2[1] - arrow_size * math.sin(angle + math.pi/6))
				])
		
		# Draw sidebar
		self._draw_sidebar()
		
		# Winner banner with better design and more prominent display
		if self.state.winner is not None:
			theme = self._get_theme_colors()
			winner = "White" if self.state.winner == PLAYER_WHITE else "Black"
			winner_emoji = "⚪" if self.state.winner == PLAYER_WHITE else "⚫"
			msg = f"{winner_emoji} {winner} Wins! {winner_emoji}"
			
			# Make the banner much more prominent
			banner = self.font_large.render(msg, True, theme.highlight_color)
			banner_rect = banner.get_rect(center=(self.config.width // 2 - 125, 50))
			bg_rect = banner_rect.inflate(80, 40)
			
			# Draw multiple layers for better visibility
			pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, border_radius=20)  # Black background
			pygame.draw.rect(self.screen, theme.card_bg, bg_rect, border_radius=20)
			pygame.draw.rect(self.screen, theme.highlight_color, bg_rect, 6, border_radius=20)
			
			# Add pulsing effect
			celebration_rect = bg_rect.inflate(30, 20)
			pygame.draw.rect(self.screen, theme.accent_color, celebration_rect, 3, border_radius=25)
			
			self.screen.blit(banner, banner_rect)
			
			# Add win reason
			win_reason = self._get_win_reason()
			reason_text = f"Reason: {win_reason}"
			reason_surf = self.font.render(reason_text, True, theme.text_color)
			reason_rect = reason_surf.get_rect(center=(self.config.width // 2 - 125, 90))
			self.screen.blit(reason_surf, reason_rect)
			
			# Add restart hint
			restart_text = "Press N for new game or ESC for menu"
			restart_surf = self.font_small.render(restart_text, True, theme.text_color)
			restart_rect = restart_surf.get_rect(center=(self.config.width // 2 - 125, 120))
			self.screen.blit(restart_surf, restart_rect)
	
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
		# Draw moving ghost with border
		theme = self._get_theme_colors()
		x1, y1 = self.point_pos(from_idx)
		x2, y2 = self.point_pos(to_idx)
		x = int(x1 + (x2 - x1) * alpha)
		y = int(y1 + (y2 - y1) * alpha)
		color = theme.white_color if self.state.to_move == PLAYER_BLACK else theme.black_color
		border_color = theme.black_color if self.state.to_move == PLAYER_BLACK else theme.white_color
		
		# Draw piece with border
		pygame.draw.circle(self.screen, color, (x, y), self.config.point_radius - 3)
		pygame.draw.circle(self.screen, border_color, (x, y), self.config.point_radius - 3, 2)
	
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
		
		# Show AI thinking indicator
		self._show_ai_thinking()
		
		# Add small delay to show thinking indicator
		pygame.time.wait(500)
		
		mv = choose_move(self.state, self.difficulty)
		if mv:
			from_idx = mv.from_idx
			to_idx = mv.to_idx
			remove_idx = mv.remove_idx
			self._apply_and_record(mv)
			if from_idx is not None and to_idx is not None:
				self.animate_move(from_idx, to_idx)
			elif remove_idx is not None:
				# AI is removing a piece - show which one
				self._highlight_removal(remove_idx)
	
	def _show_ai_thinking(self) -> None:
		"""Show AI thinking indicator"""
		theme = self._get_theme_colors()
		# Draw thinking indicator in top-left corner
		thinking_rect = pygame.Rect(20, 20, 200, 40)
		pygame.draw.rect(self.screen, theme.card_bg, thinking_rect, border_radius=8)
		pygame.draw.rect(self.screen, theme.card_border, thinking_rect, 2, border_radius=8)
		
		thinking_text = f"🤖 AI thinking... ({self.difficulty.name})"
		thinking_surf = self.font_small.render(thinking_text, True, theme.highlight_color)
		thinking_text_rect = thinking_surf.get_rect(center=thinking_rect.center)
		self.screen.blit(thinking_surf, thinking_text_rect)
	
	def _highlight_removal(self, remove_idx: int) -> None:
		"""Highlight which piece the AI is removing"""
		theme = self._get_theme_colors()
		px, py = self.point_pos(remove_idx)
		
		# Flash the piece being removed
		for _ in range(3):
			# Draw removal highlight
			pygame.draw.circle(self.screen, (255, 0, 0), (px, py), self.config.point_radius + 8, 4)
			pygame.display.flip()
			pygame.time.wait(200)
			
			# Clear highlight
			pygame.draw.circle(self.screen, theme.bg_color, (px, py), self.config.point_radius + 8)
			pygame.display.flip()
			pygame.time.wait(200)
	
	def _get_win_reason(self) -> str:
		"""Get the reason why the game ended"""
		if self.state.winner is None:
			return "Game in progress"
		
		winner = self.state.winner
		loser = -winner
		
		# Check if loser has fewer than 3 pieces
		loser_pieces = self.state.num_pieces(loser)
		if loser_pieces < 3:
			return f"Opponent reduced to {loser_pieces} pieces"
		
		# Check if loser has no legal moves
		# Temporarily switch to loser's turn to check moves
		original_turn = self.state.to_move
		self.state.to_move = loser
		legal_moves = self.state.legal_moves()
		self.state.to_move = original_turn
		
		if not legal_moves:
			return "Opponent has no legal moves"
		
		return "Game ended"
	
	def set_difficulty(self, key: int) -> None:
		self.difficulty = {pygame.K_e: EASY, pygame.K_m: MEDIUM, pygame.K_h: HARD}.get(key, self.difficulty)
	
	def handle_menu_click(self, pos: Tuple[int, int]) -> None:
		"""Handle clicks on menu screens"""
		# Check button clicks
		for i, button in enumerate(self.buttons):
			if button.contains(pos):
				if self.current_screen == Screen.WELCOME:
					if "Start Game" in button.text:  # Start Game
						self.current_screen = Screen.GAME
					elif "Learn AI" in button.text:  # Learn AI
						self._setup_ai_screen()
						self.current_screen = Screen.AI_EXPLANATION
					elif "View Rules" in button.text:  # View Rules
						self._setup_rules_screen()
						self.current_screen = Screen.RULES
					elif "Exit Game" in button.text:  # Exit Game
						return "exit"
					elif "AI:" in button.text:  # AI Status - toggle AI
						self.ai_enabled = not self.ai_enabled
						self._setup_welcome_screen()  # Refresh to show new status
				elif self.current_screen in (Screen.RULES, Screen.AI_EXPLANATION):
					if button.text == "Back":
						self._setup_welcome_screen()
						self.current_screen = Screen.WELCOME
				return
	
	def loop(self) -> None:
		running = True
		while running:
			mouse_pos = pygame.mouse.get_pos()
			
			# Update hover states
			for card in self.cards:
				card.hovered = card.contains(mouse_pos)
			for button in self.buttons:
				button.hovered = button.contains(mouse_pos)
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if self.current_screen != Screen.GAME:
						result = self.handle_menu_click(event.pos)
						if result == "exit":
							running = False
							break
					else:
						# Game screen handling
						idx = self.nearest_point(event.pos)
						if idx is not None and self.state.phase != "placing" and not self.state.removal_pending and self.state.board[idx] == self.state.to_move:
							self._dragging = True
							self._drag_from = idx
							self._selected = idx
							self._compute_legal_targets(idx)
						else:
							self.handle_click(event.pos)
				elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
					if self.current_screen == Screen.GAME and self._dragging:
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
					if event.key == pygame.K_ESCAPE:
						self._setup_welcome_screen()
						self.current_screen = Screen.WELCOME
					elif event.key == pygame.K_t:
						self._toggle_theme()
					elif event.key == pygame.K_i:
						self._show_ai_overlay = not self._show_ai_overlay
					elif event.key == pygame.K_q:
						running = False
						break
					elif self.current_screen == Screen.GAME:
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
			
			# Update AI
			if self.current_screen == Screen.GAME:
				self.maybe_ai_move()
			
			# Draw appropriate screen
			if self.current_screen == Screen.WELCOME:
				self._draw_welcome_screen()
			elif self.current_screen == Screen.RULES:
				self._draw_rules_screen()
			elif self.current_screen == Screen.AI_EXPLANATION:
				self._draw_ai_screen()
			elif self.current_screen == Screen.GAME:
				self.draw_board()
				self.update_animation()
			
			pygame.display.flip()
			self.clock.tick(60)
		
		pygame.quit()

