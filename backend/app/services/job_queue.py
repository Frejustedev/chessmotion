"""
In-memory job queue for render tasks.

Each render job runs in a background thread (ThreadPoolExecutor).
Job state is tracked in a shared dict protected by a lock.

Usage:
    job_id = queue.submit(game, settings)
    info   = queue.get(job_id)
    # info.status, info.progress, info.download_url, info.error
"""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from app.models.schemas import GameInfo, RenderSettings, RenderJobStatus
from app.services.board_renderer import BoardRenderer
from app.services.video_engine import assemble, ProgressCallback


_MAX_WORKERS = 2          # simultaneous render jobs
_MAX_STORED  = 100        # oldest jobs evicted after this count


@dataclass
class JobRecord:
    job_id:       str
    status:       RenderJobStatus = RenderJobStatus.queued
    progress:     int = 0
    message:      str = ""
    output_path:  Optional[str] = None
    download_url: Optional[str] = None
    _cb:          ProgressCallback = field(default_factory=ProgressCallback, repr=False)

    def to_dict(self) -> dict:
        return {
            "job_id":       self.job_id,
            "status":       self.status.value,
            "progress":     self.progress,
            "message":      self.message,
            "download_url": self.download_url,
        }


class RenderQueue:
    """
    Thread-safe job queue backed by a ThreadPoolExecutor.
    Suitable for a single-server deployment; replace with Celery for scale.
    """

    def __init__(self, max_workers: int = _MAX_WORKERS):
        self._pool   = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="render")
        self._jobs:  dict[str, JobRecord] = {}
        self._order: list[str] = []   # insertion order for eviction
        self._lock   = threading.Lock()

    # ── Public API ──────────────────────────────────────────────────────────────

    def submit(self, game: GameInfo, cfg: RenderSettings) -> str:
        """Queue a render job and return its job_id immediately."""
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id=job_id)

        with self._lock:
            self._jobs[job_id] = record
            self._order.append(job_id)
            self._evict_old()

        future: Future = self._pool.submit(self._run, job_id, game, cfg)
        future.add_done_callback(lambda f: self._on_future_done(job_id, f))
        logger.info(f"[JobQueue] Submitted job {job_id} ({cfg.output_format.value.upper()})")
        return job_id

    def get(self, job_id: str) -> Optional[JobRecord]:
        """Return the current JobRecord or None if unknown."""
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec and rec.status == RenderJobStatus.processing:
                # Blend: frame rendering = 0-30, assembly = 30-100 via _cb
                cb_val = rec._cb.value
                if cb_val > 0:
                    rec.progress = 30 + int(cb_val * 0.70)
            return rec

    def cancel(self, job_id: str) -> bool:
        """Mark a queued job as cancelled (running jobs cannot be stopped)."""
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec and rec.status == RenderJobStatus.queued:
                rec.status = RenderJobStatus.error
                rec.message = "Cancelled by user"
                return True
        return False

    # ── Internal ────────────────────────────────────────────────────────────────

    def _run(self, job_id: str, game: GameInfo, cfg: RenderSettings) -> None:
        """Worker: render frames + assemble video. Runs in a thread."""
        rec = self._jobs.get(job_id)
        if rec is None:
            return

        # Check if cancelled while waiting in queue
        if rec.status == RenderJobStatus.error:
            return

        self._update(job_id, status=RenderJobStatus.processing, progress=0,
                     message="Rendering frames...")

        try:
            # ── Phase 1: render frames ────────────────────────────────────────
            renderer = BoardRenderer(cfg)
            frames = renderer.render_frames_for_game(
                moves=game.moves,
                white_name=game.white.name,
                black_name=game.black.name,
                white_rating=game.white.rating,
                black_rating=game.black.rating,
                result=game.result,
                starting_fen=game.starting_fen,
            )
            self._update(job_id, progress=30, message="Assembling video...")

            # ── Phase 2: assemble video/GIF ────────────────────────────────────
            cb = rec._cb
            cb.set(0)
            out_path = assemble(frames, game, cfg, job_id, cb)

            download_url = f"/output/{out_path.name}"
            self._update(
                job_id,
                status=RenderJobStatus.done,
                progress=100,
                message="Complete",
                output_path=str(out_path),
                download_url=download_url,
            )
            logger.info(f"[JobQueue] Job {job_id} DONE -> {download_url}")

        except Exception as exc:
            logger.exception(f"[JobQueue] Job {job_id} FAILED: {exc}")
            self._update(
                job_id,
                status=RenderJobStatus.error,
                message=f"Render failed: {exc}",
            )

    def _on_future_done(self, job_id: str, future: Future) -> None:
        """Called when the thread finishes – capture any unhandled exception."""
        exc = future.exception()
        if exc:
            self._update(job_id, status=RenderJobStatus.error,
                         message=f"Unexpected error: {exc}")

    def _update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if rec is None:
                return
            for k, v in kwargs.items():
                if hasattr(rec, k):
                    setattr(rec, k, v)

    def _evict_old(self) -> None:
        """Remove completed/failed jobs if we exceed _MAX_STORED."""
        while len(self._order) > _MAX_STORED:
            old_id = self._order.pop(0)
            old = self._jobs.get(old_id)
            if old and old.status in (RenderJobStatus.done, RenderJobStatus.error):
                del self._jobs[old_id]
            else:
                # Put it back – still running
                self._order.insert(0, old_id)
                break


# ── Singleton ────────────────────────────────────────────────────────────────────
render_queue = RenderQueue()
