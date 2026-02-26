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
        from src.analytics.padel import PadelAnalytics

        metrics = compute_movement_metrics(tracks)
        report_dict["summary"] = {**report_dict["summary"], **metrics["summary"]}
        report_dict["players"] = metrics["players"]
        report_dict["status"] = "computed"

        heatmap_path = reports_dir / "heatmap.png"
        build_heatmap(tracks, heatmap_path)
        report_dict["analytics"] = {"heatmap_path": str(heatmap_path)}

        duration_s = float(video_meta.get("duration_seconds", 0))
        fps_meta = float(video_meta.get("fps", 30))
        num_frames = int(duration_s * fps_meta) if duration_s > 0 and fps_meta > 0 else max((t.get("frame", 0) for t in tracks), default=0)
        fps = fps_meta
        padel = PadelAnalytics().run_from_tracks(tracks, num_frames=num_frames, fps=fps)
        report_dict["padel"] = {
            "rally_metrics": padel["rally_metrics"],
            "shot_speeds": padel["shot_speeds"],
            "wall_usage": padel["wall_usage"],
            "player_stats_sample": padel["player_stats_data"][:5] if padel["player_stats_data"] else [],
        }
    else:
        report_dict["summary"]["total_track_points"] = 0
        report_dict["summary"]["num_players"] = 0
        report_dict["summary"]["total_distance"] = 0.0
        report_dict["summary"]["total_duration_s"] = 0.0
        report_dict["analytics"] = {}
        report_dict["padel"] = {
            "rally_metrics": [],
            "shot_speeds": [],
            "wall_usage": {"wall_bounce_count": 0, "ground_bounce_count": 0, "wall_usage_ratio": 0.0},
            "player_stats_sample": [],
        }

    write_json_atomic(report_path, report_dict)
    return report_path
