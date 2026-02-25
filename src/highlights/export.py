"""
Cut clips from match video and save highlight_*.mp4; optionally concat to one file.
Uses: video/clips (FFmpeg)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.video.clips import cut_clip, concat_clips, probe_duration
from src.utils.io import read_json, write_json_atomic, ensure_dir
from src.utils.time import now_iso


def export_highlights(
    match_dir: Path,
    video_path: Path,
    report_path: Path,
    *,
    clip_len_s: float = 12.0,
    every_s: float = 60.0,
    max_clips: int = 10,
) -> Path:
    """
    Read report, get highlight segments, cut clips, concat to highlights/highlights.mp4.
    Updates report with exported_highlights and highlights_mp4 path.
    Returns path to highlights.mp4.
    """
    report = read_json(report_path)
    from src.highlights.select import select_highlights
    segments = select_highlights(report, clip_len_s=clip_len_s, every_s=every_s, max_clips=max_clips)
    if not segments:
        duration = probe_duration(video_path)
        segments = select_highlights(
            {**report, "summary": {"match_duration_seconds": duration}},
            clip_len_s=clip_len_s, every_s=every_s, max_clips=max_clips,
        )
    if not segments:
        raise RuntimeError("No highlight segments to export")

    hdir = match_dir / "highlights"
    clips_dir = hdir / "clips"
    ensure_dir(clips_dir)
    clip_paths: List[Path] = []
    exported: List[Dict[str, Any]] = []
    for i, seg in enumerate(segments, start=1):
        out_file = clips_dir / f"highlight_{i:03d}.mp4"
        cut_clip(video_path, out_file, float(seg["start"]), float(seg["end"]))
        clip_paths.append(out_file)
        exported.append({"file": out_file.name, **seg})

    highlights_mp4 = hdir / "highlights.mp4"
    concat_clips(clip_paths, highlights_mp4)

    report["exported_highlights"] = exported
    report["highlights_mp4"] = str(highlights_mp4)
    report["last_updated_at"] = now_iso()
    write_json_atomic(report_path, report)
    return highlights_mp4
