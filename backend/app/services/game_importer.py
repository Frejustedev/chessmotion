"""
Central dispatcher: given any URL, detect the platform and delegate
to the right API client.
"""
from app.models.schemas import GameInfo
from app.services import lichess_api, chesscom_api


def _is_lichess(url: str) -> bool:
    return "lichess.org" in url


def _is_chesscom(url: str) -> bool:
    return "chess.com" in url


async def import_from_url(url: str, max_games: int = 50) -> list[GameInfo]:
    """
    Auto-detect platform from URL and return a list of GameInfo.
    Raises ValueError for unsupported URLs or API errors.
    """
    if _is_lichess(url):
        return await lichess_api.fetch_game(url, max_games=max_games)

    if _is_chesscom(url):
        return await chesscom_api.fetch_game(url, max_games=max_games)

    raise ValueError(
        "Unsupported URL. Please provide a lichess.org or chess.com link, "
        "or upload a PGN file directly."
    )
