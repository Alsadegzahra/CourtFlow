from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List


def assert_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg not found in PATH. Install it (brew install ffmpeg) and run: ffmpeg -version"
        )
    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "ffprobe not found in PATH (usually installed with ffmpeg). Run: ffprobe -version"
        )


def probe_duration_ffprobe(input_video: Path) -> float:
    """
    Returns video duration in seconds using ffprobe.
    """
    assert_ffmpeg_available()

    if not input_video.exists():
        raise FileNotFoundError(f"Input video not found: {input_video}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        str(input_video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed:\n{result.stderr}")

    info = json.loads(result.stdout)
    dur = info.get("format", {}).get("duration", None)
    if dur is None:
        raise RuntimeError(f"Could not read duration from ffprobe output for: {input_video}")

    return float(dur)


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


def concat_clips_ffmpeg(clips: List[Path], output_video: Path) -> None:
    """
    Concatenate multiple mp4 clips into a single mp4.
    Uses concat demuxer with re-encode for robustness.
    """
    assert_ffmpeg_available()

    if not clips:
        raise ValueError("No clips provided to concat")

    for c in clips:
        if not c.exists():
            raise FileNotFoundError(f"Clip not found: {c}")

    output_video.parent.mkdir(parents=True, exist_ok=True)

    # Build concat list file
    concat_list = output_video.parent / "concat_list.txt"
    concat_list.write_text(
        "\n".join([f"file '{c.as_posix()}'" for c in clips]) + "\n",
        encoding="utf-8",
    )

    # Re-encode to avoid codec mismatch issues
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_video),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed:\n{result.stderr}")