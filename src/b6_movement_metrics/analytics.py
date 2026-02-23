from __future__ import annotations

"""
Movement metrics and analytics module.

This file defines the interface that the B6 analytics team should implement:
it is responsible for turning raw tracks and calibration into a populated
Phase1Report with per-player metrics, team stats, renders references, and
highlight segments.
"""

from pathlib import Path
from typing import Optional

from src.domain.models import Phase1Report
from src.schemas import empty_report
from src.common.io_utils import write_json_atomic, read_json


def build_phase1_report(
    match: dict,
    *,
    video_meta: dict,
    tracks_path: Optional[Path],
    calib_path: Optional[Path],
    out_dir: Path,
) -> Path:
    """
    TODO(B6 analytics team): implement real movement metrics and highlights.

    Suggested behavior:
    - Start from the contract returned by `empty_report(...)` / `Phase1Report`.
    - Read tracks and calibration (if available).
    - Compute and fill at least these Phase 1 metrics:
      - Match duration (time model)
      - Heatmaps per player
      - Zone coverage distribution (court zones)
      - Net vs baseline percentage
      - Team spacing visualization / spacing stats
      - Coverage gap detection
      - Positional drift over match
      - Transition frequency (baseline → net)
      - Positional efficiency score (composite index)
      - Distance covered
      - Average and maximum speed
      - Sprint count
      - Acceleration / deceleration indicators
      - Lateral movement percentage
      - Movement intensity timeline
      - Load distribution across the match (early / mid / late)
      - Motion-based fatigue / intensity drop-off trends
    - Populate `players`, `team`, `summary`, and `renders` with these metrics.
    - Populate `highlights` with movement-intensity-based segments that will
      drive Stage 06 highlight export.
    - Write the finished report to `out_dir / 'reports' / 'report.json'`.
    - Return the path to the report file.
    """
    # For now, we just create the contract-shaped placeholder report.
    report_dict = empty_report(
        match_id=match["match_id"],
        court_id=match["court_id"],
        video_meta=video_meta,
    )

    reports_dir = out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "report.json"

    write_json_atomic(report_path, report_dict)
    return report_path

