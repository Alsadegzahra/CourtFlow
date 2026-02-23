from __future__ import annotations

"""
Coordinate conversion module.

This file defines the interface that the B5b coord conversion team should
implement: using a CalibrationHomography, enrich TrackRecord entries with
court-space coordinates (x_court, y_court) derived from image-space pixels.
"""

from pathlib import Path
from typing import List

from src.domain.models import CalibrationHomography, TrackRecord, Tracks
from src.common.io_utils import read_json, write_json_atomic


def apply_calibration_to_tracks(
    tracks_path: Path,
    calib: CalibrationHomography,
) -> None:
    """
    TODO(B5b coord conversion team): map pixel coordinates to court coordinates.

    Suggested behavior:
    - Load tracks from `tracks_path` (list of dicts following `TrackRecord`).
    - For each record, compute `x_court` / `y_court` using `calib.homography`.
    - Write the updated tracks back to the same JSON file (atomic write).
    """
    raise NotImplementedError("Coordinate conversion is not implemented yet.")


def load_tracks_from_json(tracks_path: Path) -> Tracks:
    """
    Convenience loader used by both pipeline and tests.
    """
    raw = read_json(tracks_path)
    return [TrackRecord(**item) for item in raw]


def dump_tracks_to_json(tracks_path: Path, tracks: Tracks) -> None:
    """
    Convenience dumper to keep serialization consistent across teams.
    """
    payload: List[dict] = [t.__dict__ for t in tracks]
    write_json_atomic(tracks_path, payload)

