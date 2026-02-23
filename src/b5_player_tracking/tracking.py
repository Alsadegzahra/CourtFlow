from __future__ import annotations

"""
Player detection and tracking module.

This file defines the interface that the B5 player tracking team should
implement: given a match video, produce a list of TrackRecord entries and
persist them to tracks/tracks.json for downstream stages to consume.
"""

from pathlib import Path
from typing import List

from src.domain.models import TrackRecord, Tracks


def run_player_tracking(
    video_path: Path,
    out_dir: Path,
) -> Path:
    """
    TODO(B5 player tracking team): implement detection + tracking and write tracks.

    Expected behavior once implemented:
    - Run a player detector + tracker on `video_path`.
    - Produce a list of `TrackRecord` instances (or plain dicts with the same fields)
      for all detections across the match.
    - Serialize them as JSON to `out_dir / 'tracks' / 'tracks.json'` using the
      contract in `TrackRecord`.
    - Return the path to the written tracks file.
    """
    raise NotImplementedError("Player tracking is not implemented yet.")


def validate_tracks_contract(tracks: Tracks) -> None:
    """
    TODO(B5 player tracking team): add stricter validation if needed.

    This helper is intended to be called in tests and in the pipeline to assert that
    all produced track records conform to the Phase 1 contract (types, ranges, etc.).
    """
    # For now we keep this intentionally minimal; teams can extend as they learn more.
    for t in tracks:
        if t.frame < 0:
            raise ValueError(f"Invalid frame index in track: {t}")

