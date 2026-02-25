"""
Build Phase1Report (small JSON) from metrics + metadata.
Uses: analytics/movement, analytics/heatmap, utils/io, domain/report_contract
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.report_contract import empty_report
from src.utils.io import read_json, write_json_atomic


def build_phase1_report(
    match: dict,
    *,
    video_meta: dict,
    tracks_path: Optional[Path] = None,
    calib_path: Optional[Path] = None,
    out_dir: Path,
) -> Path:
    """Build report.json from video meta and tracks. Fills summary, players, and heatmap from tracks."""
    report_dict = empty_report(
        match_id=match["match_id"],
        court_id=match["court_id"],
        video_meta=video_meta,
    )
    reports_dir = out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "report.json"

    tracks: list = []
    if tracks_path and tracks_path.exists():
        raw = read_json(tracks_path)
        if isinstance(raw, list):
            tracks = raw

    if tracks:
        from src.analytics.movement import compute_movement_metrics
        from src.analytics.heatmap import build_heatmap

        metrics = compute_movement_metrics(tracks)
        report_dict["summary"] = {**report_dict["summary"], **metrics["summary"]}
        report_dict["players"] = metrics["players"]
        report_dict["status"] = "computed"

        heatmap_path = reports_dir / "heatmap.png"
        build_heatmap(tracks, heatmap_path)
        report_dict["analytics"] = {"heatmap_path": str(heatmap_path)}
    else:
        report_dict["summary"]["total_track_points"] = 0
        report_dict["summary"]["num_players"] = 0
        report_dict["summary"]["total_distance"] = 0.0
        report_dict["summary"]["total_duration_s"] = 0.0
        report_dict["analytics"] = {}

    write_json_atomic(report_path, report_dict)
    return report_path
