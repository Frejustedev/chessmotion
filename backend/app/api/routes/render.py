import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.schemas import (
    GameInfo, RenderSettings, RenderJobResponse, RenderJobStatus,
)
from app.services.job_queue import render_queue

router = APIRouter()


class StartRenderBody(BaseModel):
    game: GameInfo
    settings: RenderSettings = RenderSettings()


@router.post(
    "/start",
    response_model=RenderJobResponse,
    summary="Start a render job",
    description=(
        "Submit a GameInfo + RenderSettings to queue an async MP4/GIF render. "
        "Returns a job_id immediately. Poll `/status/{job_id}` for progress."
    ),
)
async def start_render(body: StartRenderBody):
    job_id = render_queue.submit(body.game, body.settings)
    return RenderJobResponse(
        job_id=job_id,
        status=RenderJobStatus.queued,
        progress=0,
        message="Job queued",
    )


@router.get(
    "/status/{job_id}",
    response_model=RenderJobResponse,
    summary="Poll render job status",
    description="Returns current status (queued/processing/done/error) and progress 0-100.",
)
async def get_render_status(job_id: str):
    rec = render_queue.get(job_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return RenderJobResponse(
        job_id=rec.job_id,
        status=rec.status,
        progress=rec.progress,
        message=rec.message,
        download_url=rec.download_url,
    )


@router.post(
    "/upload-music",
    summary="Upload a background music file",
    description="Accepts MP3, WAV, OGG. Returns the filename to use in RenderSettings.background_music.",
)
async def upload_music(file: UploadFile = File(...)):
    from app.core.config import settings as cfg
    allowed = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format '{suffix}'. Use: {allowed}")

    safe_name = f"upload_{uuid.uuid4().hex[:8]}{suffix}"
    dest = cfg.ASSETS_DIR / "sounds" / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Music file too large (max 50 MB).")
    dest.write_bytes(content)
    return {"filename": safe_name, "original_name": file.filename, "size_kb": len(content) // 1024}


@router.delete(
    "/cancel/{job_id}",
    summary="Cancel a queued job",
)
async def cancel_render(job_id: str):
    cancelled = render_queue.cancel(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job not found or already running/completed.",
        )
    return {"detail": "Job cancelled."}


@router.get(
    "/download/{job_id}",
    summary="Download the rendered file",
    description="Returns the MP4 or GIF file. Job must have status='done'.",
)
async def download_render(job_id: str):
    rec = render_queue.get(job_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    if rec.status != RenderJobStatus.done:
        raise HTTPException(
            status_code=425,
            detail=f"Job not ready (status: {rec.status.value}, progress: {rec.progress}%).",
        )

    path = Path(rec.output_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Output file no longer available.")

    media_type = "video/mp4" if path.suffix == ".mp4" else "image/gif"
    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=path.name,
    )
