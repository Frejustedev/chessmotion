"""
Stockfish evaluator – wraps chess.engine for position analysis.
Singleton engine instance reused across all render jobs.
Falls back gracefully (returns None) when Stockfish is not installed.
"""
from __future__ import annotations

from typing import Optional
import chess
import chess.engine
from loguru import logger

from app.core.config import settings

_engine: Optional[chess.engine.SimpleEngine] = None
_init_attempted = False

# Common locations to search if STOCKFISH_PATH is empty
_CANDIDATES = [
    "stockfish",
    "/usr/games/stockfish",
    "/usr/bin/stockfish",
    "/usr/local/bin/stockfish",
    r"C:\Users\Public\stockfish\stockfish.exe",
]


def _init_engine() -> Optional[chess.engine.SimpleEngine]:
    global _engine, _init_attempted
    if _init_attempted:
        return _engine
    _init_attempted = True

    paths = [settings.STOCKFISH_PATH] + _CANDIDATES if settings.STOCKFISH_PATH else _CANDIDATES
    for path in paths:
        if not path:
            continue
        try:
            eng = chess.engine.SimpleEngine.popen_uci(path)
            eng.configure({"Threads": 1, "Hash": 16})
            _engine = eng
            logger.info(f"[Stockfish] Engine ready at: {path}")
            return _engine
        except Exception:
            continue

    logger.warning("[Stockfish] Not found – eval bar will be disabled. "
                   "Install stockfish or set STOCKFISH_PATH in .env")
    return None


def evaluate_positions(fens: list[str], depth: int = 14) -> list[Optional[float]]:
    """
    Evaluate a list of FEN positions. Returns centipawns from White's perspective.
    Positive = White advantage. Mate scores clamped to ±9900.
    Returns a list of None if engine unavailable.
    """
    engine = _init_engine()
    if engine is None:
        return [None] * len(fens)

    results: list[Optional[float]] = []
    for fen in fens:
        try:
            board = chess.Board(fen)
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            score = info["score"].white()
            if score.is_mate():
                m = score.mate()
                cp: Optional[float] = 9900.0 if m and m > 0 else -9900.0
            else:
                cp = float(score.score() or 0)
            results.append(cp)
        except Exception as exc:
            logger.warning(f"[Stockfish] Analysis error: {exc}")
            results.append(None)
    return results


def close_engine() -> None:
    global _engine
    if _engine:
        try:
            _engine.quit()
        except Exception:
            pass
        _engine = None
