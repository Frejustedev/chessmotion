"""
Lichess API client.

Supported URL patterns:
  - Single game  : https://lichess.org/{gameId}
  - Game PGN     : https://lichess.org/game/export/{gameId}
  - Study        : https://lichess.org/study/{studyId}
  - Tournament   : https://lichess.org/tournament/{tourneyId}
  - User games   : https://lichess.org/@/{username}  (fetches last game)
"""
import re
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.models.schemas import GameInfo
from app.services.pgn_parser import parse_pgn_string


LICHESS_BASE = "https://lichess.org"

# Regex patterns for different URL types
_PATTERNS = {
    "game":       re.compile(r"lichess\.org/([A-Za-z0-9]{8,12})(?:[#?/]|$)"),
    "game_export":re.compile(r"lichess\.org/game/export/([A-Za-z0-9]{8,12})"),
    "study":      re.compile(r"lichess\.org/study/([A-Za-z0-9]+)"),
    "tournament": re.compile(r"lichess\.org/tournament/([A-Za-z0-9]+)"),
    "user":       re.compile(r"lichess\.org/@/([A-Za-z0-9_-]+)"),
}


def _build_headers() -> dict:
    headers = {"Accept": "application/x-chess-pgn"}
    if settings.LICHESS_TOKEN:
        headers["Authorization"] = f"Bearer {settings.LICHESS_TOKEN}"
    return headers


def _detect_url_type(url: str) -> tuple[str, str]:
    """Return (url_type, identifier) or raise ValueError."""
    # Check game export first (more specific)
    for kind in ("game_export", "game", "study", "tournament", "user"):
        m = _PATTERNS[kind].search(url)
        if m:
            return kind, m.group(1)
    raise ValueError(f"Unrecognised Lichess URL format: {url}")


async def fetch_game(url: str, max_games: int = 50) -> list[GameInfo]:
    """
    Fetch one or several games from any Lichess URL.
    Returns a list of GameInfo (may contain >1 item for tournaments/users).
    """
    url_type, identifier = _detect_url_type(url)
    logger.info(f"[Lichess] type={url_type}, id={identifier}")

    async with httpx.AsyncClient(timeout=30) as client:
        pgn_text = await _fetch_pgn(client, url_type, identifier, max_games)

    games = parse_pgn_string(pgn_text)
    logger.info(f"[Lichess] Parsed {len(games)} game(s)")
    return games


async def _fetch_pgn(
    client: httpx.AsyncClient,
    url_type: str,
    identifier: str,
    max_games: int,
) -> str:
    headers = _build_headers()

    if url_type in ("game", "game_export"):
        endpoint = f"{LICHESS_BASE}/game/export/{identifier}"
        params = {"clocks": "true", "opening": "true", "literate": "false"}
        resp = await client.get(endpoint, headers=headers, params=params)

    elif url_type == "study":
        endpoint = f"{LICHESS_BASE}/api/study/{identifier}.pgn"
        params = {"clocks": "true", "comments": "true"}
        resp = await client.get(endpoint, headers=headers, params=params)

    elif url_type == "tournament":
        endpoint = f"{LICHESS_BASE}/api/tournament/{identifier}/games"
        params = {"max": max_games, "opening": "true", "clocks": "true"}
        resp = await client.get(endpoint, headers=headers, params=params)

    elif url_type == "user":
        endpoint = f"{LICHESS_BASE}/api/games/user/{identifier}"
        params = {"max": max_games, "opening": "true", "clocks": "true"}
        resp = await client.get(endpoint, headers=headers, params=params)

    else:
        raise ValueError(f"Unknown url_type: {url_type}")

    _raise_for_status(resp, "Lichess")
    return resp.text


def _raise_for_status(resp: httpx.Response, platform: str) -> None:
    if resp.status_code == 404:
        raise ValueError(f"{platform}: game not found (404).")
    if resp.status_code == 429:
        raise ValueError(f"{platform}: rate limit exceeded – please wait and retry.")
    if resp.status_code >= 400:
        raise ValueError(f"{platform}: API error {resp.status_code} – {resp.text[:200]}")
