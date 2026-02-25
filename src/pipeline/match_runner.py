"""
Orchestrates ONCE-PER-MATCH sequential stages (no parallel).
Uses: court/registry, court/calibration/artifacts, video/frames_opencv, vision/*,
      storage/tracks_db, analytics/report, highlights/export, pipeline/paths, pipeline/stages.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from src.config.settings import ensure_dirs
from src.pipeline.paths import match_dir, ensure_match_dirs
from src.pipeline import stages
from src.storage.match_db import (
    get_match,
    update_match,
    add_artifact,
)


@dataclass
class HighlightConfig:
    clip_len_s: float = 12.0
    every_s: float = 60.0
    max_clips: int = 10


def run_match(
    match_id: str,
    cfg: Optional[HighlightConfig] = None,
) -> Path:
    """
    Run full pipeline for one match: load match from DB, ensure dirs, run stages 01–06,
    register HIGHLIGHTS_MP4 artifact, set state DONE/FAILED.
    Returns path to highlights.mp4.
    """
    cfg = cfg or HighlightConfig()
    ensure_dirs()

    match = get_match(match_id)
    if not match:
        raise ValueError(f"Match not found: {match_id}")

    # New layout: output_dir must be data/matches/<match_id>
    out_dir = Path(match["output_dir"])
    if out_dir != match_dir(match_id):
        out_dir = match_dir(match_id)
    ensure_match_dirs(match_id)

    source_type = match["source_type"]
    source_uri = match["source_uri"]
    # Prefer ingested raw/match.mp4 if present
    raw_mp4 = out_dir / "raw" / "match.mp4"
    if raw_mp4.exists():
        video_path = raw_mp4
    else:
        video_path = Path(source_uri)
    if source_type != "FILE" or not video_path.exists():
        raise FileNotFoundError(f"Match video not found: {video_path}")

    update_match(match_id, state="PROCESSING")

    try:
        stages.ensure_meta_and_report(out_dir, video_path)
        stages.update_meta_status(out_dir, "running")

        print("\n[01] Load calibration")
        stages.stage_01_load_calibration(out_dir, match["court_id"], video_path)
        print("\n[02] Player detection + tracking")
        stages.stage_02_track(out_dir, video_path)
        print("\n[03] Coordinate mapping")
        stages.stage_03_map(out_dir, match["court_id"])
        print("\n[04] Analytics report")
        stages.stage_04_report(out_dir, match)
        print("\n[05] Render overlays")
        stages.stage_05_renders(out_dir)
        print("\n[06] Export highlights")
        highlights_mp4 = stages.stage_06_highlights(
            out_dir,
            video_path,
            clip_len_s=cfg.clip_len_s,
            every_s=cfg.every_s,
            max_clips=cfg.max_clips,
        )

        stages.update_meta_status(out_dir, "pipeline_complete")
        add_artifact(
            match_id,
            "HIGHLIGHTS_MP4",
            str(highlights_mp4),
            status="READY",
            size_bytes=highlights_mp4.stat().st_size if highlights_mp4.exists() else None,
        )
        update_match(match_id, state="DONE")
        print("\n✅ Pipeline finished.")
        return highlights_mp4

    except Exception as e:
        update_match(match_id, state="FAILED", last_error=str(e))
        raise
