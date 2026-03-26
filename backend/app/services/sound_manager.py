"""
Sound manager – generates/caches WAV sound effects programmatically
so the app works out-of-the-box without any external audio assets.

Generated sounds:
  move.wav    – short click / wood-knock
  capture.wav – slightly louder thud
  check.wav   – short rising tone

Background music is optional (user-supplied or silence).
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


_SAMPLE_RATE = 44100


def _write_wav(path: Path, samples: list[float], rate: int = _SAMPLE_RATE) -> None:
    """Write a mono 16-bit PCM WAV file from a list of float samples in [-1, 1]."""
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            wf.writeframes(struct.pack("<h", int(clamped * 32767)))


def _sine(freq: float, duration: float, rate: int = _SAMPLE_RATE,
          amplitude: float = 0.5, decay: float = 6.0) -> list[float]:
    """Generate a decaying sine wave."""
    n = int(duration * rate)
    return [
        amplitude * math.sin(2 * math.pi * freq * t / rate) * math.exp(-decay * t / rate)
        for t in range(n)
    ]


def _noise_burst(duration: float, rate: int = _SAMPLE_RATE,
                 amplitude: float = 0.3, decay: float = 15.0) -> list[float]:
    """Band-limited noise burst for a wood-knock effect."""
    import random
    n = int(duration * rate)
    rng = random.Random(42)
    return [
        amplitude * rng.uniform(-1, 1) * math.exp(-decay * t / rate)
        for t in range(n)
    ]


def _mix(*signals: list[float]) -> list[float]:
    length = max(len(s) for s in signals)
    result = [0.0] * length
    for sig in signals:
        for i, v in enumerate(sig):
            result[i] += v
    # Normalize
    peak = max(abs(v) for v in result) or 1.0
    if peak > 0.95:
        result = [v / peak * 0.95 for v in result]
    return result


def _ensure_sound(path: Path, generator_fn) -> Path:
    if not path.exists():
        logger.info(f"[Sound] Generating {path.name}...")
        samples = generator_fn()
        _write_wav(path, samples)
    return path


def get_sound_dir() -> Path:
    d = settings.ASSETS_DIR / "sounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_move_sound() -> Path:
    p = get_sound_dir() / "move.wav"
    return _ensure_sound(p, lambda: _mix(
        _noise_burst(0.08, amplitude=0.4, decay=25.0),
        _sine(800, 0.06, amplitude=0.15, decay=30.0),
    ))


def get_capture_sound() -> Path:
    p = get_sound_dir() / "capture.wav"
    return _ensure_sound(p, lambda: _mix(
        _noise_burst(0.12, amplitude=0.6, decay=18.0),
        _sine(400, 0.10, amplitude=0.20, decay=20.0),
        _sine(600, 0.08, amplitude=0.10, decay=22.0),
    ))


def get_check_sound() -> Path:
    p = get_sound_dir() / "check.wav"
    return _ensure_sound(p, lambda: _mix(
        _sine(880, 0.12, amplitude=0.30, decay=8.0),
        _sine(1100, 0.10, amplitude=0.20, decay=10.0),
        _sine(1320, 0.08, amplitude=0.15, decay=12.0),
    ))


def get_background_music(user_path: Optional[str] = None) -> Optional[Path]:
    """
    Return path to background music file.
    user_path must be a bare filename (no path separators) resolved inside
    assets/sounds/. Absolute paths and directory traversal are rejected.
    """
    if not user_path:
        return None
    # Security: reject any path separator to prevent directory traversal
    if any(sep in user_path for sep in ("/", "\\", "..")):
        logger.warning(f"[Sound] Rejected suspicious music path: {user_path!r}")
        return None
    candidate = get_sound_dir() / Path(user_path).name  # .name strips any remaining dirs
    if candidate.exists():
        return candidate
    logger.warning(f"[Sound] Background music not found: {user_path}")
    return None
