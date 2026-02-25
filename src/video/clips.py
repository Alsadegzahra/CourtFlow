"""
FFmpeg clipper: cut and concat clips (used by highlights export).
Uses: subprocess ffmpeg
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import List


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and ffprobe must be in PATH.")


def probe_duration(video_path: Path) -> float:
    _check_ffmpeg()
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", str(video_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {r.stderr}")
    return float(json.loads(r.stdout).get("format", {}).get("duration", 0))


def cut_clip(input_video: Path, output_video: Path, start_s: float, end_s: float) -> None:
    _check_ffmpeg()
    if end_s <= start_s:
        raise ValueError(f"Invalid clip: start={start_s}, end={end_s}")
    output_video.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", str(start_s), "-to", str(end_s), "-i", str(input_video),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-movflags", "+faststart", str(output_video),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg cut failed: {r.stderr}")


def concat_clips(clip_paths: List[Path], output_video: Path) -> None:
    _check_ffmpeg()
    if not clip_paths:
        raise ValueError("No clips to concat")
    for p in clip_paths:
        if not p.exists():
            raise FileNotFoundError(f"Clip not found: {p}")
    output_video.parent.mkdir(parents=True, exist_ok=True)
    list_file = output_video.parent / "concat_list.txt"
    list_file.write_text("\n".join([f"file '{p.as_posix()}'" for p in clip_paths]) + "\n", encoding="utf-8")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac",
        "-movflags", "+faststart", str(output_video),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {r.stderr}")
