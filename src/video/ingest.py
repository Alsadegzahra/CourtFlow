"""
FFmpeg: RTSP -> match.mp4 (recording per match) or file -> match.mp4.
Uses: court/config (optional), subprocess ffmpeg, config/settings
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from src.config.settings import DEFAULT_FPS, ensure_dirs
from src.utils.io import ensure_dir


def _check_ffmpeg() -> None:
    import shutil
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not found in PATH. Install it (e.g. brew install ffmpeg).")


def ingest_file_to_mp4(
    input_path: Path,
    output_mp4: Path,
    *,
    fps: int = DEFAULT_FPS,
    width: int = 1920,
    height: int = 1080,
    video_bitrate: str = "8M",
    audio_bitrate: str = "128k",
) -> Path:
    """Re-encode a file to a single match.mp4. Creates parent dirs."""
    _check_ffmpeg()
    ensure_dirs()
    ensure_dir(output_mp4.parent)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-b:v", video_bitrate, "-preset", "veryfast",
        "-r", str(fps), "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", audio_bitrate,
        "-movflags", "+faststart", str(output_mp4),
    ]
    subprocess.run(cmd, check=True)
    return output_mp4
