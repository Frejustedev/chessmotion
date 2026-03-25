from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.schemas import GameInfo, UrlImportRequest
from app.services.pgn_parser import parse_pgn_bytes
from app.services.game_importer import import_from_url

router = APIRouter()


@router.post(
    "/parse-pgn",
    response_model=list[GameInfo],
    summary="Parse an uploaded PGN file",
    description=(
        "Upload a `.pgn` file (single or multi-game). "
        "Returns a list of normalised GameInfo objects, one per game found."
    ),
)
async def parse_pgn(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pgn"):
        raise HTTPException(status_code=400, detail="Only .pgn files are accepted.")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:  # 10 MB guard
        raise HTTPException(status_code=413, detail="PGN file too large (max 10 MB).")

    try:
        games = parse_pgn_bytes(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return games


@router.post(
    "/import-url",
    response_model=list[GameInfo],
    summary="Import game(s) from a Lichess or Chess.com URL",
    description=(
        "Accepts any Lichess or Chess.com URL (single game, tournament, user profile). "
        "Returns a list of normalised GameInfo objects."
    ),
)
async def import_url(
    body: UrlImportRequest,
    max_games: int = Query(default=50, ge=1, le=200, description="Max games to fetch for bulk URLs"),
):
    url_str = str(body.url)
    try:
        games = await import_from_url(url_str, max_games=max_games)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"External API error: {exc}")

    return games


@router.get(
    "/preview/{game_index}",
    response_model=GameInfo,
    summary="Extract one game by index from a previously parsed list",
    description="Helper to pick a specific game by index from a multi-game import result.",
)
async def preview_game(
    game_index: int,
    games: list[GameInfo] = [],
):
    # This endpoint is mainly for documentation; the frontend handles indexing client-side.
    raise HTTPException(
        status_code=400,
        detail="Use /parse-pgn or /import-url and select game_index client-side.",
    )
