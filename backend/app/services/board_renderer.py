"""
Board renderer – generates one PIL Image (frame) per chess position.

Architecture:
  BoardRenderer.render_frame(fen, last_move_uci, settings) -> PIL.Image.Image

The frame contains:
  ┌─────────────────────────────────┐
  │  [eval bar]  Header (names)     │
  │              8x8 board          │
  │              Footer (result)    │
  └─────────────────────────────────┘
"""
from __future__ import annotations

import re
from typing import Optional

import chess
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

from app.models.schemas import RenderSettings, BoardTheme, PieceSet
from app.services.piece_manager import PieceManager


# ── Board theme colour palettes ──────────────────────────────────────────────────
_THEMES: dict[str, dict] = {
    "green": {
        "light": (238, 238, 210),
        "dark":  (118, 150, 86),
        "highlight_light": (246, 246, 130),
        "highlight_dark":  (186, 202, 68),
        "border": (40, 40, 40),
        "bg": (30, 30, 30),
        "text": (220, 220, 220),
        "coord_light": (118, 150, 86),
        "coord_dark":  (238, 238, 210),
    },
    "wood": {
        "light": (240, 217, 181),
        "dark":  (181, 136, 99),
        "highlight_light": (205, 210, 106),
        "highlight_dark":  (170, 162, 58),
        "border": (80, 40, 10),
        "bg": (60, 30, 10),
        "text": (240, 220, 180),
        "coord_light": (181, 136, 99),
        "coord_dark":  (240, 217, 181),
    },
    "dark": {
        "light": (90, 90, 110),
        "dark":  (40, 40, 55),
        "highlight_light": (120, 130, 80),
        "highlight_dark":  (80, 90, 50),
        "border": (15, 15, 20),
        "bg": (15, 15, 20),
        "text": (200, 200, 220),
        "coord_light": (40, 40, 55),
        "coord_dark":  (90, 90, 110),
    },
    "blue": {
        "light": (222, 231, 243),
        "dark":  (82, 121, 170),
        "highlight_light": (227, 230, 140),
        "highlight_dark":  (164, 175, 84),
        "border": (30, 50, 80),
        "bg": (20, 40, 70),
        "text": (210, 225, 245),
        "coord_light": (82, 121, 170),
        "coord_dark":  (222, 231, 243),
    },
    "purple": {
        "light": (235, 220, 245),
        "dark":  (130, 90, 160),
        "highlight_light": (240, 235, 130),
        "highlight_dark":  (180, 160, 60),
        "border": (50, 20, 70),
        "bg": (35, 15, 55),
        "text": (230, 210, 245),
        "coord_light": (130, 90, 160),
        "coord_dark":  (235, 220, 245),
    },
}

_COORD_LABELS_FILES = list("abcdefgh")
_COORD_LABELS_RANKS = list("87654321")

# Size ratio constants (relative to square_size)
_HEADER_H_RATIO = 0.7      # header height = sq * ratio
_COORD_W_RATIO  = 0.35     # coordinate strip width = sq * ratio
_EVAL_W_RATIO   = 0.45     # eval bar width = sq * ratio
_PIECE_PAD      = 0.04     # piece padding inside square (fraction of sq)


class BoardRenderer:
    """
    Stateless renderer: call render_frame() as many times as needed.
    Piece images are cached internally by (piece_set, square_size).
    """

    def __init__(self, render_settings: RenderSettings):
        self.s = render_settings
        self.sq = render_settings.board_size // 8
        self.theme = _THEMES.get(render_settings.board_theme.value, _THEMES["green"])
        self._piece_mgr: Optional[PieceManager] = None

        # Pre-compute layout dimensions
        self.coord_w  = int(self.sq * _COORD_W_RATIO) if self.s.show_coordinates else 0
        self.eval_w   = int(self.sq * _EVAL_W_RATIO)  if self.s.show_eval_bar    else 0
        self.header_h = int(self.sq * _HEADER_H_RATIO) if self.s.show_player_names else 0
        self.footer_h = int(self.sq * _HEADER_H_RATIO) if self.s.show_result else 0

        # Total canvas size
        self.board_px = self.sq * 8
        self.total_w  = self.eval_w + self.coord_w + self.board_px + self.coord_w
        self.total_h  = self.header_h + self.coord_w + self.board_px + self.footer_h

        # Fonts
        self._font_coord  = self._load_font(int(self.sq * 0.22))
        self._font_header = self._load_font(int(self.sq * 0.30))
        self._font_result = self._load_font(int(self.sq * 0.35), bold=True)

        # Pre-compute font heights once (getbbox is reliable across Pillow versions)
        self._coord_fh  = self._font_height(self._font_coord)
        self._header_fh = self._font_height(self._font_header)
        self._result_fh = self._font_height(self._font_result)

    # ── Public API ────────────────────────────────────────────────────────────────

    def render_frame(
        self,
        fen: str,
        last_move_uci: Optional[str] = None,
        eval_score: Optional[float] = None,
        move_number: Optional[int] = None,
        white_name: str = "White",
        black_name: str = "Black",
        white_rating: Optional[int] = None,
        black_rating: Optional[int] = None,
        result: str = "*",
        white_clock: Optional[str] = None,
        black_clock: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Image.Image:
        """
        Render a single board position to a PIL Image.
        last_move_uci: UCI string like "e2e4" to highlight squares, or None.
        eval_score:    centipawns (positive = white advantage).
        """
        board = chess.Board(fen)
        last_squares = _uci_to_squares(last_move_uci)

        canvas = Image.new("RGB", (self.total_w, self.total_h), self.theme["bg"])
        draw = ImageDraw.Draw(canvas)

        ox = self.eval_w  # x-offset for the coord+board area

        # Header – black player on top (or white if flipped)
        if self.header_h:
            top_name    = black_name if not self.s.flip_board else white_name
            top_rating  = white_rating if self.s.flip_board else None
            bot_name    = white_name if not self.s.flip_board else black_name
            bot_rating  = white_rating if not self.s.flip_board else None
            top_clock   = black_clock if not self.s.flip_board else white_clock
            bot_clock   = white_clock if not self.s.flip_board else black_clock
            self._draw_player_bar(draw, canvas, ox, 0,
                                  top_name, black_rating if not self.s.flip_board else white_rating,
                                  top_clock, is_top=True)

        # Board origin
        bx = ox + self.coord_w
        by = self.header_h + self.coord_w

        # Draw squares + highlights
        self._draw_squares(draw, bx, by, last_squares)

        # Coordinates
        if self.coord_w:
            self._draw_coords(draw, bx, by)

        # Pieces
        self._draw_pieces(canvas, board, bx, by)

        # Eval bar
        if self.eval_w and eval_score is not None:
            self._draw_eval_bar(draw, eval_score)

        # Footer – white player at bottom
        if self.footer_h:
            fy = self.header_h + self.coord_w + self.board_px
            self._draw_player_bar(draw, canvas, ox, fy,
                                  white_name if not self.s.flip_board else black_name,
                                  white_rating if not self.s.flip_board else black_rating,
                                  bot_clock if self.header_h else white_clock,
                                  is_top=False,
                                  result=result if self.s.show_result else None)

        # Commentary overlay (shown if settings request it)
        if self.s.show_comments and comment:
            self._draw_commentary(canvas, draw, comment)

        return canvas

    def render_frames_for_game(
        self,
        moves: list,          # list[MoveInfo]
        white_name: str = "White",
        black_name: str = "Black",
        white_rating: Optional[int] = None,
        black_rating: Optional[int] = None,
        result: str = "*",
        starting_fen: str = chess.STARTING_FEN,
    ) -> list[Image.Image]:
        """
        Render one frame per position: starting position + one per move.
        Returns len(moves)+1 frames.
        """
        frames: list[Image.Image] = []

        # Frame 0 – starting position
        frames.append(self.render_frame(
            fen=starting_fen,
            white_name=white_name, black_name=black_name,
            white_rating=white_rating, black_rating=black_rating,
            result="*",
        ))

        prev_uci = None
        for i, move in enumerate(moves):
            frame = self.render_frame(
                fen=move.fen_after,
                last_move_uci=move.uci,
                eval_score=move.eval_score,
                move_number=i + 1,
                white_name=white_name, black_name=black_name,
                white_rating=white_rating, black_rating=black_rating,
                result=result if i == len(moves) - 1 else "*",
                white_clock=move.clock if i % 2 == 1 else None,
                black_clock=move.clock if i % 2 == 0 else None,
                comment=move.comment,
            )
            frames.append(frame)

        logger.info(f"[BoardRenderer] Generated {len(frames)} frames")
        return frames

    # ── Private drawing helpers ────────────────────────────────────────────────────

    def _draw_squares(self, draw: ImageDraw.ImageDraw, bx: int, by: int,
                      highlighted: set[int]) -> None:
        for rank in range(8):
            for file in range(8):
                sq_idx = (7 - rank) * 8 + file if not self.s.flip_board else rank * 8 + (7 - file)
                is_light = (rank + file) % 2 == 0
                if sq_idx in highlighted:
                    color = self.theme["highlight_light"] if is_light else self.theme["highlight_dark"]
                else:
                    color = self.theme["light"] if is_light else self.theme["dark"]

                x0 = bx + file * self.sq
                y0 = by + rank * self.sq
                draw.rectangle([x0, y0, x0 + self.sq - 1, y0 + self.sq - 1], fill=color)

    def _draw_coords(self, draw: ImageDraw.ImageDraw, bx: int, by: int) -> None:
        pad = max(1, self.coord_w // 6)
        for i in range(8):
            # Rank numbers (left strip)
            rank_label = _COORD_LABELS_RANKS[i] if not self.s.flip_board else _COORD_LABELS_RANKS[7 - i]
            sq_i = (7 - i) * 8  # leftmost square in this row
            is_light_rank = (i % 2 == 0)
            text_color = self.theme["coord_dark"] if is_light_rank else self.theme["coord_light"]
            y_center = by + i * self.sq + self.sq // 2
            draw.text(
                (bx - self.coord_w + pad, y_center - self._coord_fh // 2),
                rank_label, fill=text_color, font=self._font_coord,
            )

            # File letters (bottom strip)
            file_label = _COORD_LABELS_FILES[i] if not self.s.flip_board else _COORD_LABELS_FILES[7 - i]
            is_light_file = (i % 2 == 0)
            text_color2 = self.theme["coord_dark"] if is_light_file else self.theme["coord_light"]
            x_center = bx + i * self.sq + self.sq // 2
            draw.text(
                (x_center - self._font_coord.size // 3, by + self.board_px + pad),
                file_label, fill=text_color2, font=self._font_coord,
            )

    def _draw_pieces(self, canvas: Image.Image, board: chess.Board, bx: int, by: int) -> None:
        if self._piece_mgr is None:
            self._piece_mgr = PieceManager(self.s.piece_set, self.sq)

        pad = int(self.sq * _PIECE_PAD)
        piece_size = self.sq - 2 * pad

        for rank in range(8):
            for file in range(8):
                sq_idx = (7 - rank) * 8 + file if not self.s.flip_board else rank * 8 + (7 - file)
                piece = board.piece_at(sq_idx)
                if piece is None:
                    continue

                piece_img = self._piece_mgr.get(piece.symbol())
                if piece_img.size != (piece_size, piece_size):
                    piece_img = piece_img.resize((piece_size, piece_size), Image.LANCZOS)

                x = bx + file * self.sq + pad
                y = by + rank * self.sq + pad
                canvas.paste(piece_img, (x, y), mask=piece_img)

    def _draw_player_bar(
        self, draw: ImageDraw.ImageDraw, canvas: Image.Image,
        ox: int, oy: int,
        name: str, rating: Optional[int], clock: Optional[str],
        is_top: bool, result: Optional[str] = None,
    ) -> None:
        bar_w = self.total_w - ox
        bar_h = self.header_h
        # Background
        bar_color = tuple(max(0, c - 15) for c in self.theme["bg"])
        draw.rectangle([ox, oy, ox + bar_w, oy + bar_h], fill=bar_color)

        # Name + rating
        display = name
        if rating:
            display += f" ({rating})"
        tx = ox + self.coord_w + 8
        ty = oy + (bar_h - self._header_fh) // 2
        draw.text((tx, ty), display, fill=self.theme["text"], font=self._font_header)

        # Clock
        if clock:
            cw = draw.textlength(clock, font=self._font_header)
            draw.text(
                (ox + bar_w - cw - 12, ty),
                clock, fill=self.theme["text"], font=self._font_header,
            )

        # Result badge
        if result and result != "*":
            badge_map = {"1-0": ("1-0", (80, 160, 80)), "0-1": ("0-1", (180, 70, 70)),
                         "1/2-1/2": ("½-½", (160, 160, 60))}
            badge_text, badge_color = badge_map.get(result, (result, (120, 120, 120)))
            bw = int(draw.textlength(badge_text, font=self._font_result)) + 16
            bh = int(self._result_fh * 1.4)
            bx_ = ox + bar_w - bw - 8
            by_ = oy + (bar_h - bh) // 2
            draw.rounded_rectangle([bx_, by_, bx_ + bw, by_ + bh], radius=4, fill=badge_color)
            draw.text((bx_ + 8, by_ + (bh - self._result_fh) // 2),
                      badge_text, fill=(255, 255, 255), font=self._font_result)

    def _draw_commentary(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, text: str) -> None:
        """
        Draw a semi-transparent commentary banner at the bottom of the board area.
        Wraps long text automatically.
        """
        avg_char_w = max(6, self._coord_fh // 2)
        max_chars = max(20, (self.board_px - 12) // avg_char_w)
        # Simple word-wrap
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if len(test) > max_chars and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        lines = lines[:3]  # max 3 lines

        line_h = self._coord_fh + 4
        banner_h = len(lines) * line_h + 8
        bx = self.eval_w + self.coord_w
        by = self.header_h + self.coord_w + self.board_px - banner_h

        # Semi-transparent overlay via RGBA paste
        overlay = Image.new("RGBA", (self.board_px, banner_h), (0, 0, 0, 180))
        canvas.paste(overlay, (bx, by), overlay)

        draw2 = ImageDraw.Draw(canvas)
        for j, line in enumerate(lines):
            draw2.text(
                (bx + 6, by + 4 + j * line_h),
                line, fill=(255, 255, 200), font=self._font_coord,
            )

    def _draw_eval_bar(self, draw: ImageDraw.ImageDraw, eval_score: float) -> None:
        """
        Draw a vertical evaluation bar on the left.
        Positive eval_score = white advantage (top portion = white).
        """
        bar_x = 0
        bar_y = self.header_h
        bar_h = self.coord_w + self.board_px

        # Clamp to ±6 pawns for display
        clamped = max(-600, min(600, eval_score))
        # Fraction of bar that belongs to white (top)
        white_frac = 0.5 + (clamped / 1200.0)
        white_h = int(bar_h * (1.0 - white_frac))  # white is at bottom visually
        black_h = bar_h - white_h

        draw.rectangle([bar_x, bar_y, bar_x + self.eval_w, bar_y + black_h],
                       fill=(30, 30, 30))
        draw.rectangle([bar_x, bar_y + black_h, bar_x + self.eval_w, bar_y + bar_h],
                       fill=(230, 230, 230))

        # Score label
        score_str = _format_eval(eval_score)
        lx = bar_x + self.eval_w // 2
        ly = bar_y + black_h
        txt_color = (230, 230, 230) if white_frac < 0.5 else (30, 30, 30)
        draw.text((lx, ly), score_str,
                  fill=txt_color, font=self._font_coord, anchor="mm")

    @staticmethod
    def _font_height(font) -> int:
        """Return ascent+descent height of a font object regardless of type."""
        try:
            return font.size
        except AttributeError:
            bb = font.getbbox("Ag")
            return bb[3] - bb[1]

    @staticmethod
    def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Load a system font, falling back gracefully."""
        candidates = (["arialbd.ttf", "Arial Bold.ttf"] if bold else
                      ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf"])
        for name in candidates:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default(size=size)


# ── Utilities ─────────────────────────────────────────────────────────────────────

def _uci_to_squares(uci: Optional[str]) -> set[int]:
    """Convert a UCI move string like 'e2e4' to a set of two square indices."""
    if not uci or len(uci) < 4:
        return set()
    try:
        move = chess.Move.from_uci(uci)
        return {move.from_square, move.to_square}
    except Exception:
        return set()


def _format_eval(cp: float) -> str:
    """Format centipawns as a readable string."""
    if abs(cp) >= 900:
        return f"M{abs(int((1000 - abs(cp)) // 10))}"
    pawns = cp / 100.0
    sign = "+" if pawns >= 0 else ""
    return f"{sign}{pawns:.1f}"
