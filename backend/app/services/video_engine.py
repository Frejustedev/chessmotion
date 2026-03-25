"""
Video engine – assembles PIL frames + audio into MP4 or GIF.

Public surface:
  assemble(frames, game, settings, job) -> Path
    Writes file to OUTPUT_DIR/{job_id}.{ext} and returns its Path.
    Calls job.set_progress(pct) so the caller can track progress.
"""
from __future__ import annotations

import gc
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

import chess
import numpy as np
from PIL import Image
from loguru import logger

from app.core.config import settings
from app.models.schemas import GameInfo, RenderSettings
from app.services.sound_manager import (
    get_move_sound, get_capture_sound, get_check_sound, get_background_music
)


# Make MoviePy less verbose
os.environ.setdefault("MOVIEPY_FFMPEG_OPTS", "")


class ProgressCallback:
    """Lightweight object passed to assemble() to track progress."""
    def __init__(self):
        self._pct: int = 0

    def set(self, pct: int) -> None:
        self._pct = min(100, max(0, pct))

    @property
    def value(self) -> int:
        return self._pct


def assemble(
    frames: list[Image.Image],
    game: GameInfo,
    cfg: RenderSettings,
    job_id: str,
    progress: ProgressCallback,
) -> Path:
    """
    Main entry point. Returns the path of the written output file.
    Delegates to _build_mp4 or _build_gif.
    """
    out_dir = settings.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = cfg.output_format.value   # "mp4" or "gif"
    out_path = out_dir / f"{job_id}.{ext}"

    logger.info(f"[VideoEngine] Starting {ext.upper()} assembly – {len(frames)} frames, delay={cfg.move_delay}s")

    if ext == "gif":
        _build_gif(frames, cfg, out_path, progress)
    else:
        _build_mp4(frames, game, cfg, out_path, progress)

    logger.info(f"[VideoEngine] Done -> {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


# ── MP4 builder ────────────────────────────────────────────────────────────────

def _build_mp4(
    frames: list[Image.Image],
    game: GameInfo,
    cfg: RenderSettings,
    out_path: Path,
    progress: ProgressCallback,
) -> None:
    from moviepy.editor import (
        ImageSequenceClip, CompositeAudioClip, AudioFileClip,
        concatenate_audioclips, AudioClip,
    )
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe

    n = len(frames)
    fps = max(1, round(1.0 / cfg.move_delay))  # e.g. 1.0s delay → 1 fps

    progress.set(5)

    # ── Convert frames to numpy arrays ──────────────────────────────────────────
    logger.debug("[VideoEngine] Converting frames to numpy arrays...")
    np_frames = [np.array(f.convert("RGB")) for f in frames]
    progress.set(20)

    # ── Build silent video clip ──────────────────────────────────────────────────
    # Use a higher fps internally then hold each frame for move_delay seconds
    hold_frames = max(1, round(cfg.move_delay * 24))  # 24 fps internal
    internal_fps = 24

    expanded: list[np.ndarray] = []
    for i, arr in enumerate(np_frames):
        expanded.extend([arr] * hold_frames)
        if i % max(1, n // 10) == 0:
            progress.set(20 + int(i / n * 25))

    video_clip = ImageSequenceClip(expanded, fps=internal_fps)
    total_duration = video_clip.duration
    progress.set(50)

    # ── Build audio ───────────────────────────────────────────────────────────────
    audio_clips = []

    if cfg.sound_effects:
        logger.debug("[VideoEngine] Building sound effects timeline...")
        move_snd    = get_move_sound()
        capture_snd = get_capture_sound()
        check_snd   = get_check_sound()

        for i, move in enumerate(game.moves):
            t = (i + 1) * cfg.move_delay   # time offset for this move's sound
            if t > total_duration:
                break

            # Determine sound type from move data
            board_before = chess.Board(
                game.moves[i - 1].fen_after if i > 0 else game.starting_fen
            )
            board_after = chess.Board(move.fen_after)

            if board_after.is_check():
                snd_path = check_snd
            elif board_before.is_capture(chess.Move.from_uci(move.uci)):
                snd_path = capture_snd
            else:
                snd_path = move_snd

            try:
                clip = AudioFileClip(str(snd_path)).set_start(t)
                audio_clips.append(clip)
            except Exception as exc:
                logger.warning(f"[VideoEngine] SFX load error: {exc}")

        progress.set(65)

    # ── Background music ──────────────────────────────────────────────────────────
    music_path = get_background_music(cfg.background_music)
    if music_path:
        try:
            music = AudioFileClip(str(music_path))
            if music.duration < total_duration:
                loops = int(total_duration / music.duration) + 1
                from moviepy.editor import concatenate_audioclips as cat
                music = cat([music] * loops).subclip(0, total_duration)
            else:
                music = music.subclip(0, total_duration)
            music = music.volumex(0.3)  # lower background music volume
            audio_clips.append(music)
        except Exception as exc:
            logger.warning(f"[VideoEngine] Background music error: {exc}")

    progress.set(70)

    # ── Composite audio + write ────────────────────────────────────────────────
    if audio_clips:
        composite_audio = CompositeAudioClip(audio_clips)
        final = video_clip.set_audio(composite_audio)
    else:
        final = video_clip

    logger.debug(f"[VideoEngine] Writing MP4 to {out_path}...")
    final.write_videofile(
        str(out_path),
        codec="libx264",
        audio_codec="aac",
        fps=internal_fps,
        preset="fast",
        ffmpeg_params=["-crf", "23"],
        logger=None,          # suppress moviepy progress bar
    )

    # Cleanup
    for c in audio_clips:
        try:
            c.close()
        except Exception:
            pass
    video_clip.close()
    gc.collect()
    progress.set(100)


# ── GIF builder ───────────────────────────────────────────────────────────────

def _build_gif(
    frames: list[Image.Image],
    cfg: RenderSettings,
    out_path: Path,
    progress: ProgressCallback,
) -> None:
    """
    Build an animated GIF using Pillow.
    Frames are quantized to 256 colours with dithering for best quality.
    """
    n = len(frames)
    delay_ms = int(cfg.move_delay * 1000)

    logger.debug(f"[VideoEngine] Quantizing {n} frames for GIF...")
    quantized: list[Image.Image] = []

    for i, frame in enumerate(frames):
        # Quantize to palette with dithering
        q = frame.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=1)
        quantized.append(q)
        if i % max(1, n // 10) == 0:
            progress.set(10 + int(i / n * 75))

    progress.set(88)
    logger.debug(f"[VideoEngine] Saving GIF to {out_path}...")

    quantized[0].save(
        str(out_path),
        format="GIF",
        save_all=True,
        append_images=quantized[1:],
        loop=0,          # loop forever
        duration=delay_ms,
        optimize=False,  # faster; enable for smaller files at cost of speed
    )
    progress.set(100)
