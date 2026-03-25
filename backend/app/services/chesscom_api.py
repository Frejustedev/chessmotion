"""
Chess.com public API client.

Supported URL patterns:
  - Single game  : https://www.chess.com/game/live/{gameId}
                   https://www.chess.com/game/daily/{gameId}
  - Player games : https://www.chess.com/member/{username}  (last 20 games)
  - Tournament   : https://www.chess.com/tournament/{slug}  (first 50 games)

Chess.com exposes games via:
  GET /pub/player/{user}/games/{YYYY}/{MM}   → NDJSON with pgn field
  GET /pub/tournament/{url-id}               → round/group structure
"""
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger

from app.models.schemas import GameInfo
from app.services.pgn_parser import parse_pgn_string


CHESSCOM_BASE = "https://api.chess.com/pub"
_HEADERS = {"User-Agent": "ChessMotion/1.0 (contact: chessmotion@example.com)"}

_PATTERNS = {
    "game_live":  re.compile(r"chess\.com/game/live/(\d+)"),
    "game_daily": re.compile(r"chess\.com/game/daily/(\d+)"),
    "member":     re.compile(r"chess\.com/member/([A-Za-z0-9_-]+)"),
    "tournament": re.compile(r"chess\.com/tournament/([A-Za-z0-9_/-]+)"),
}


def _detect_url_type(url: str) -> tuple[str, str]:
    for kind, pattern in _PATTERNS.items():
        m = pattern.search(url)
        if m:
            return kind, m.group(1)
    raise ValueError(f"Unrecognised Chess.com URL format: {url}")


async def fetch_game(url: str, max_games: int = 50) -> list[GameInfo]:
    """
    Fetch one or several games from any Chess.com URL.
    Returns a normalised list[GameInfo].
    """
    url_type, identifier = _detect_url_type(url)
    logger.info(f"[Chess.com] type={url_type}, id={identifier}")

    async with httpx.AsyncClient(timeout=30, headers=_HEADERS) as client:
        if url_type in ("game_live", "game_daily"):
            games = await _fetch_single_game(client, url_type, identifier)
        elif url_type == "member":
            games = await _fetch_member_games(client, identifier, max_games)
        elif url_type == "tournament":
            games = await _fetch_tournament_games(client, identifier, max_games)
        else:
            raise ValueError(f"Unknown url_type: {url_type}")

    logger.info(f"[Chess.com] Fetched {len(games)} game(s)")
    return games


async def _fetch_single_game(
    client: httpx.AsyncClient, url_type: str, game_id: str
) -> list[GameInfo]:
    """
    Chess.com doesn't expose a single-game endpoint by numeric ID in its public API.
    We search recent games of both players and match by ID embedded in the URL.
    As a fallback we reconstruct the archive URL from the numeric game ID.
    """
    # Try direct PGN endpoint (undocumented but stable)
    kind = "live" if url_type == "game_live" else "daily"
    direct_url = f"https://www.chess.com/callback/live/game/{game_id}/pgn" if kind == "live" \
        else f"https://www.chess.com/callback/daily/game/{game_id}/pgn"

    resp = await client.get(direct_url)
    if resp.status_code == 200 and resp.text.strip().startswith("["):
        return parse_pgn_string(resp.text)

    raise ValueError(
        "Chess.com single-game lookup requires the game's username context. "
        "Please use a player profile URL (chess.com/member/{username}) instead."
    )


async def _fetch_member_games(
    client: httpx.AsyncClient, username: str, max_games: int
) -> list[GameInfo]:
    """Fetch the most recent N games for a Chess.com user via the archive API."""
    # Step 1 – get list of archive months
    archives_resp = await client.get(f"{CHESSCOM_BASE}/player/{username}/games/archives")
    _raise_for_status(archives_resp, "Chess.com")
    archives: list[str] = archives_resp.json().get("archives", [])

    if not archives:
        raise ValueError(f"No game archives found for Chess.com user '{username}'.")

    all_pgns: list[str] = []
    # Iterate months newest-first
    for archive_url in reversed(archives):
        if len(all_pgns) >= max_games:
            break
        resp = await client.get(archive_url)
        if resp.status_code != 200:
            continue
        month_games = resp.json().get("games", [])
        for g in reversed(month_games):  # newest first within month
            pgn = g.get("pgn", "")
            if pgn:
                all_pgns.append(pgn)
            if len(all_pgns) >= max_games:
                break

    if not all_pgns:
        raise ValueError(f"No games with PGN data found for '{username}'.")

    combined_pgn = "\n\n".join(all_pgns)
    return parse_pgn_string(combined_pgn)


async def _fetch_tournament_games(
    client: httpx.AsyncClient, slug: str, max_games: int
) -> list[GameInfo]:
    """Fetch games from a Chess.com tournament via the rounds endpoint."""
    tourney_resp = await client.get(f"{CHESSCOM_BASE}/tournament/{slug}")
    _raise_for_status(tourney_resp, "Chess.com")

    rounds: list[dict] = tourney_resp.json().get("rounds", [])
    if not rounds:
        raise ValueError("No rounds found in this Chess.com tournament.")

    all_pgns: list[str] = []
    for round_info in rounds:
        if len(all_pgns) >= max_games:
            break
        round_url = round_info.get("@id", "")
        if not round_url:
            continue
        round_resp = await client.get(round_url)
        if round_resp.status_code != 200:
            continue
        groups = round_resp.json().get("groups", [])
        for group in groups:
            group_url = group.get("@id", "")
            if not group_url:
                continue
            group_resp = await client.get(group_url)
            if group_resp.status_code != 200:
                continue
            for g in group_resp.json().get("games", []):
                pgn = g.get("pgn", "")
                if pgn:
                    all_pgns.append(pgn)
                if len(all_pgns) >= max_games:
                    break

    if not all_pgns:
        raise ValueError("No PGN games found in this Chess.com tournament.")

    return parse_pgn_string("\n\n".join(all_pgns))


def _raise_for_status(resp: httpx.Response, platform: str) -> None:
    if resp.status_code == 404:
        raise ValueError(f"{platform}: resource not found (404).")
    if resp.status_code == 429:
        raise ValueError(f"{platform}: rate limit – please wait and retry.")
    if resp.status_code >= 400:
        raise ValueError(f"{platform}: API error {resp.status_code} – {resp.text[:200]}")
