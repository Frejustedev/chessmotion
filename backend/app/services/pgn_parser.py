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


# NAG code → display symbol
_NAG_SYMBOLS: dict[int, str] = {
    1: "!",   2: "?",   3: "!!",  4: "??",
    5: "!?",  6: "?!",  7: "□",   10: "=",
    13: "∞",  14: "⩲",  15: "⩱",  16: "±",
    17: "∓",  18: "+−", 19: "−+",
}


def _nag_symbol(nags: set[int]) -> Optional[str]:
    """Return the most important NAG symbol, priority: !!/??/?!/!?/!/? """
    priority = [3, 4, 5, 6, 1, 2, 18, 19, 16, 17, 14, 15, 13, 10]
    for n in priority:
        if n in nags:
            return _NAG_SYMBOLS[n]
    return None


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
    nag = _nag_symbol(node.nags)

    return MoveInfo(
        san=san,
        uci=uci,
        fen_after=fen_after,
        comment=comment,
        clock=clock,
        nag=nag,
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


def parse_pgn_string(
    pgn_text: str,
    limit: int = 200,
    skip: int = 0,
) -> tuple[list[GameInfo], int]:
    """
    Parse a PGN string, return (games, total_count).
    Uses streaming to count headers without decoding every move, then
    fully parses only the requested page.
    """
    # Fast pass: count total games by scanning for [Event] tags
    total = pgn_text.count("\n[Event ") + (1 if pgn_text.lstrip().startswith("[Event ") else 0)

    stream = io.StringIO(pgn_text)
    collected: list[chess.pgn.Game] = []
    idx = 0

    while len(collected) < limit:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        if idx >= skip:
            collected.append(game)
        idx += 1

    # Count remaining if our fast pass was inaccurate
    if total < idx:
        total = idx
        while True:
            g = chess.pgn.read_game(stream)
            if g is None:
                break
            total += 1

    if total == 0:
        raise ValueError("No valid games found in the provided PGN.")

    return [_game_to_schema(g, total_games=total) for g in collected], total


def parse_pgn_bytes(
    raw: bytes,
    limit: int = 200,
    skip: int = 0,
) -> tuple[list[GameInfo], int]:
    """Accept raw bytes (file upload) and decode to string before parsing."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Unable to decode PGN file – unsupported encoding.")
    return parse_pgn_string(text, limit=limit, skip=skip)
