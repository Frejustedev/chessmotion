from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


# ── Enumerations ────────────────────────────────────────────────────────────────

class OutputFormat(str, Enum):
    mp4 = "mp4"
    gif = "gif"


class BoardTheme(str, Enum):
    wood = "wood"
    green = "green"
    dark = "dark"
    blue = "blue"
    purple = "purple"


class PieceSet(str, Enum):
    staunton = "staunton"
    neo = "neo"
    alpha = "alpha"
    merida = "merida"


# ── Input Models ────────────────────────────────────────────────────────────────

class CommentaryStyle(str, Enum):
    none        = "none"
    grandmaster = "grandmaster"
    casual      = "casual"
    coach       = "coach"


class RenderSettings(BaseModel):
    output_format: OutputFormat = OutputFormat.mp4
    move_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Seconds between moves")
    board_theme: BoardTheme = BoardTheme.green
    piece_set: PieceSet = PieceSet.staunton
    board_size: int = Field(default=800, ge=200, le=2000, description="Board image size in pixels")
    show_coordinates: bool = True
    show_player_names: bool = True
    show_result: bool = True
    show_comments: bool = True
    show_eval_bar: bool = False
    flip_board: bool = False
    background_music: Optional[str] = None
    sound_effects: bool = True
    highlight_last_move: bool = True
    game_index: int = Field(default=0, ge=0, description="Index for multi-game PGN")
    commentary_style: CommentaryStyle = CommentaryStyle.none
    show_move_arrow: bool = True
    show_nag: bool = True
    show_captured_pieces: bool = True
    show_opening_name: bool = True


class UrlImportRequest(BaseModel):
    url: HttpUrl
    settings: RenderSettings = RenderSettings()


# ── Output / Normalized Game ─────────────────────────────────────────────────────

class PlayerInfo(BaseModel):
    name: str = "Unknown"
    rating: Optional[int] = None
    title: Optional[str] = None


class MoveInfo(BaseModel):
    san: str
    uci: str
    fen_after: str
    comment: Optional[str] = None
    eval_score: Optional[float] = None  # centipawns, populated if stockfish enabled
    clock: Optional[str] = None
    nag: Optional[str] = None           # e.g. "!!", "?", "!?" from PGN annotations


class GameInfo(BaseModel):
    white: PlayerInfo
    black: PlayerInfo
    result: str = "*"
    event: Optional[str] = None
    site: Optional[str] = None
    date: Optional[str] = None
    opening: Optional[str] = None
    moves: list[MoveInfo] = []
    starting_fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    total_games: int = 1  # for multi-game PGNs


# ── Render Job ────────────────────────────────────────────────────────────────────

class RenderJobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    error = "error"


class PgnParseResult(BaseModel):
    games: list["GameInfo"]
    total: int
    limit: int
    skip: int


class RenderJobResponse(BaseModel):
    job_id: str
    status: RenderJobStatus
    progress: int = Field(default=0, ge=0, le=100)
    message: str = ""
    download_url: Optional[str] = None


class BatchStartBody(BaseModel):
    games: list["GameInfo"]
    settings: RenderSettings = RenderSettings()


class BatchStartResponse(BaseModel):
    job_ids: list[str]
    total: int
