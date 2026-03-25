"""
PGN parser – converts one or many games in a PGN string/file into
the normalised GameInfo schema understood by the rest of the app.
"""
import re
import io
from typing import Optional

import chess
import chess.pgn

from app.models.schemas import GameInfo, MoveInfo, PlayerInfo


def _extract_clock(comment: str) -> Optional[str]:
    """Pull clock annotation like [%clk 0:01:23] from a comment string."""
    match = re.search(r"\[%clk\s+([\d:]+)\]", comment)
    return match.group(1) if match else None


def _clean_comment(comment: str) -> Optional[str]:
    """Remove engine / clock annotations, return human-readable text or None."""
    cleaned = re.sub(r"\[%[^\]]+\]", "", comment).strip()
    return cleaned if cleaned else None


def _node_to_move(node: chess.pgn.ChildNode, board_before: chess.Board) -> MoveInfo:
    """Convert a pgn ChildNode to a MoveInfo, then push the move onto board_before."""
    move = node.move
    san = board_before.san(move)
    uci = move.uci()

    board_before.push(move)
    fen_after = board_before.fen()

    raw_comment = node.comment or ""
    clock = _extract_clock(raw_comment)
    comment = _clean_comment(raw_comment)

    return MoveInfo(
        san=san,
        uci=uci,
        fen_after=fen_after,
        comment=comment,
        clock=clock,
    )


def _game_to_schema(game: chess.pgn.Game, total_games: int = 1) -> GameInfo:
    """Convert a python-chess Game object to a GameInfo Pydantic model."""
    headers = game.headers

    def parse_rating(val: Optional[str]) -> Optional[int]:
        try:
            return int(val) if val and val != "?" else None
        except ValueError:
            return None

    white = PlayerInfo(
        name=headers.get("White", "Unknown"),
        rating=parse_rating(headers.get("WhiteElo")),
        title=headers.get("WhiteTitle") or None,
    )
    black = PlayerInfo(
        name=headers.get("Black", "Unknown"),
        rating=parse_rating(headers.get("BlackElo")),
        title=headers.get("BlackTitle") or None,
    )

    # Walk the main line only (no variations)
    moves: list[MoveInfo] = []
    board = game.board()
    node = game

    for child in game.mainline():
        moves.append(_node_to_move(child, board))

    starting_fen = headers.get("FEN", chess.STARTING_FEN)

    return GameInfo(
        white=white,
        black=black,
        result=headers.get("Result", "*"),
        event=headers.get("Event") or None,
        site=headers.get("Site") or None,
        date=headers.get("Date") or None,
        opening=headers.get("Opening") or None,
        moves=moves,
        starting_fen=starting_fen,
        total_games=total_games,
    )


def parse_pgn_string(pgn_text: str) -> list[GameInfo]:
    """Parse a full PGN string (may contain multiple games) and return a list."""
    stream = io.StringIO(pgn_text)
    games: list[GameInfo] = []

    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        games.append(game)   # collect raw games first to know total count

    total = len(games)
    if total == 0:
        raise ValueError("No valid games found in the provided PGN.")

    return [_game_to_schema(g, total_games=total) for g in games]


def parse_pgn_bytes(raw: bytes) -> list[GameInfo]:
    """Accept raw bytes (file upload) and decode to string before parsing."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Unable to decode PGN file – unsupported encoding.")
    return parse_pgn_string(text)
