"""
Piece image manager.

Downloads SVG piece sets from the Lichess CDN on first use,
converts them to RGBA PNGs via cairosvg, and caches them on disk.
Falls back to programmatically drawn pieces (Pillow) if download fails.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

from app.core.config import settings
from app.models.schemas import PieceSet


# ── Lichess CDN mapping ─────────────────────────────────────────────────────────
#   piece set name  →  lichess theme folder
_LICHESS_THEME: dict[str, str] = {
    "staunton": "cburnett",
    "neo":      "neo",
    "alpha":    "alpha",
    "merida":   "merida",
}

# Piece codes used in Lichess CDN filenames
# Format: {color}{PIECE_UPPER}.svg  e.g. "wK.svg", "bQ.svg"
_PIECES = ["K", "Q", "R", "B", "N", "P"]
_COLORS = ["w", "b"]

# Map chess.Board piece symbols to our file naming
_SYMBOL_MAP = {
    "K": "K", "Q": "Q", "R": "R", "B": "B", "N": "N", "P": "P",
    "k": "K", "q": "Q", "r": "R", "b": "B", "n": "N", "p": "P",
}
_COLOR_MAP = {
    "K": "w", "Q": "w", "R": "w", "B": "w", "N": "w", "P": "w",
    "k": "b", "q": "b", "r": "b", "b": "b", "n": "b", "p": "b",
}

# Unicode chess symbols for fallback renderer
_UNICODE_PIECES = {
    "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
}


class PieceManager:
    """
    Loads (or generates) all 12 piece images for a given piece set at a given size.
    Returns PIL RGBA images keyed by piece symbol string (e.g. "wK", "bN").
    """

    def __init__(self, piece_set: PieceSet, size: int):
        self.piece_set = piece_set
        self.size = size
        self._cache_dir = settings.ASSETS_DIR / "pieces" / piece_set.value
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._images: dict[str, Image.Image] = {}

    def get(self, symbol: str) -> Image.Image:
        """Return piece image for a board symbol like 'K','p','n', etc."""
        color = _COLOR_MAP[symbol]
        piece = _SYMBOL_MAP[symbol]
        key = f"{color}{piece}"
        if key not in self._images:
            self._images[key] = self._load(key)
        return self._images[key]

    def _load(self, key: str) -> Image.Image:
        """Try disk cache → CDN download → fallback renderer."""
        cached_path = self._cache_dir / f"{key}_{self.size}.png"

        if cached_path.exists():
            return Image.open(cached_path).convert("RGBA")

        img = self._download_svg(key)
        if img is None:
            img = self._draw_fallback(key)

        img.save(cached_path, "PNG")
        return img

    def _download_svg(self, key: str) -> Optional[Image.Image]:
        """Download SVG from Lichess CDN and rasterize it."""
        try:
            import cairosvg
            theme = _LICHESS_THEME.get(self.piece_set.value, "cburnett")
            url = f"https://lichess1.org/assets/piece/{theme}/{key}.svg"
            resp = httpx.get(url, timeout=10, follow_redirects=True)
            if resp.status_code != 200:
                logger.warning(f"[PieceManager] CDN {url} → {resp.status_code}")
                return None
            png_bytes = cairosvg.svg2png(
                bytestring=resp.content,
                output_width=self.size,
                output_height=self.size,
            )
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            logger.debug(f"[PieceManager] Downloaded {key} from CDN")
            return img
        except Exception as exc:
            logger.warning(f"[PieceManager] SVG download failed for {key}: {exc}")
            return None

    def _draw_fallback(self, key: str) -> Image.Image:
        """
        Draw a clean, readable piece using Pillow primitives.
        White pieces = white circle + dark symbol; Black pieces = dark circle + white symbol.
        """
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        is_white = key.startswith("w")
        # Circle colours
        fill   = (245, 245, 245, 230) if is_white else (40, 40, 40, 230)
        border = (60, 60, 60, 255)    if is_white else (200, 200, 200, 255)
        text_c = (30, 30, 30, 255)    if is_white else (240, 240, 240, 255)

        pad = max(2, s // 12)
        draw.ellipse([pad, pad, s - pad, s - pad], fill=fill, outline=border, width=max(1, s // 40))

        symbol = _UNICODE_PIECES.get(key, key[1])
        font_size = int(s * 0.55)
        try:
            font = ImageFont.truetype("seguisym.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (s - tw) // 2 - bbox[0]
        y = (s - th) // 2 - bbox[1]
        draw.text((x, y), symbol, fill=text_c, font=font)
        return img


def preload_pieces(piece_set: PieceSet, size: int) -> PieceManager:
    """Convenience factory that eagerly downloads all 12 pieces."""
    manager = PieceManager(piece_set, size)
    for color in _COLORS:
        for piece in _PIECES:
            key = f"{color}{piece}"
            logger.debug(f"[PieceManager] Preloading {piece_set.value}/{key}")
            manager._load(key)
    return manager
