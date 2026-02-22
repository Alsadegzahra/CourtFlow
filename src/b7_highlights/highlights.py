# src/b7_highlights/highlights.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.common.ffmpeg_utils import (
    probe_duration_ffprobe,
    cut_clip_ffmpeg,
    concat_clips_ffmpeg,
)


@dataclass(frozen=True)
class HighlightConfig:
    clip_len_s: float = 12.0
    every_s: float = 60.0
    max_clips: int = 10


def generate_dummy_highlights(
    input_video: Path,
    out_dir: Path,
    config: Optional[HighlightConfig] = None,
) -> Path:
    """
    Dummy highlights:
      - probe duration
      - cut clip_len_s clips every every_s seconds (up to max_clips)
      - concatenate into out_dir/highlights.mp4

    Returns:
      Path to highlights.mp4
    """
    config = config or HighlightConfig()

    if not input_video.exists():
        raise FileNotFoundError(f"Input video not found: {input_video}")

    out_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    duration = probe_duration_ffprobe(input_video)

    clips: List[Path] = []
    for i in range(config.max_clips):
        start = i * config.every_s
        if start >= duration:
            break

        end = min(start + config.clip_len_s, duration)
        if end <= start:
            break

        clip_path = clips_dir / f"clip_{i:02d}.mp4"
        cut_clip_ffmpeg(
            input_video=input_video,
            output_video=clip_path,
            start_time=float(start),
            end_time=float(end),
        )
        clips.append(clip_path)

    if not clips:
        raise RuntimeError("No highlight clips were generated (video may be too short).")

    highlights_path = out_dir / "highlights.mp4"
    concat_clips_ffmpeg(clips, highlights_path)
    return highlights_path