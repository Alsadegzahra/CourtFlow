# src/b1_capture/recorder_ffmpeg.py
from __future__ import annotations

import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.common.config import INPUT_VIDEOS_DIR, ensure_dirs
from src.common.ffmpeg_utils import assert_ffmpeg_available
from src.common.io_utils import write_json, ensure_dir


@dataclass(frozen=True)
class ChunkRecordConfig:
    chunk_sec: int = 300            # 5 minutes
    fps: int = 30
    width: int = 1920
    height: int = 1080
    video_bitrate: str = "8M"
    audio_bitrate: str = "128k"


def record_file_to_chunks(
    input_path: str,
    chunks_dir: str,
    *,
    chunk_sec: int = 300,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    video_bitrate: str = "8M",
    audio_bitrate: str = "128k",
) -> List[Path]:
    """
    MVP: Reads a FILE and writes time-based chunks to chunks_dir/chunk_%05d.mp4.

    Returns: list of chunk paths sorted by filename.

    Notes:
    - We re-encode to consistent format to keep downstream stable.
    - Later: add RTSP support + atomic .part rename.
    """
    assert_ffmpeg_available()
    ensure_dirs()

    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    chunks_path = Path(chunks_dir)
    chunks_path.mkdir(parents=True, exist_ok=True)
    out_pattern = str(chunks_path / "chunk_%05d.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_path),
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-preset", "veryfast",
        "-r", str(fps),
        "-vf",
        (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        ),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-f", "segment",
        "-segment_time", str(chunk_sec),
        "-reset_timestamps", "1",
        out_pattern,
    ]

    subprocess.run(cmd, check=True)

    chunks = sorted(chunks_path.glob("chunk_*.mp4"))
    if not chunks:
        raise RuntimeError(f"No chunks were produced in: {chunks_path}")

    return chunks


def record_match_file_to_chunks(
    match_id: str,
    input_video_file: str,
    config: Optional[ChunkRecordConfig] = None,
) -> dict:
    """
    CourtFlow-friendly wrapper:
    - creates: data/input_videos/<match_id>/chunks/
    - writes chunks
    - writes a manifest json
    - returns dict with paths

    This is what B3 should call.
    """
    config = config or ChunkRecordConfig()
    ensure_dirs()

    match_dir = INPUT_VIDEOS_DIR / match_id
    chunks_dir = match_dir / "chunks"
    ensure_dir(chunks_dir)

    chunks = record_file_to_chunks(
        input_path=input_video_file,
        chunks_dir=str(chunks_dir),
        chunk_sec=config.chunk_sec,
        fps=config.fps,
        width=config.width,
        height=config.height,
        video_bitrate=config.video_bitrate,
        audio_bitrate=config.audio_bitrate,
    )

    manifest = {
        "match_id": match_id,
        "source_file": str(Path(input_video_file).resolve()),
        "created_at_epoch": int(time.time()),
        "chunk_sec": config.chunk_sec,
        "fps": config.fps,
        "width": config.width,
        "height": config.height,
        "video_bitrate": config.video_bitrate,
        "audio_bitrate": config.audio_bitrate,
        "chunks": [c.name for c in chunks],
        "chunks_dir": str(chunks_dir),
    }

    write_json(match_dir / "chunks_manifest.json", manifest)

    return {
        "match_id": match_id,
        "chunks_dir": str(chunks_dir),
        "chunks": [str(c) for c in chunks],
        "manifest_path": str(match_dir / "chunks_manifest.json"),
    }