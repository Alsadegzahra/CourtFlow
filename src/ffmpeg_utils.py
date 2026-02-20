from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def assert_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg not found in PATH. Install it (brew install ffmpeg) and run: ffmpeg -version"
        )


def cut_clip_ffmpeg(
    input_video: Path,
    output_video: Path,
    start_time: float,
    end_time: float,
) -> None:
    """
    Cut a clip using FFmpeg.
    -ss before -i is fast seeking.
    We re-encode for reliability across files (copy mode can fail depending on keyframes).
    """
    assert_ffmpeg_available()

    if end_time <= start_time:
        raise ValueError(f"Invalid clip window: start={start_time}, end={end_time}")

    output_video.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", str(input_video),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_video),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")
