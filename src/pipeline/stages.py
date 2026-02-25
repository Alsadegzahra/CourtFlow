"""
Stage functions: calibration, track, map, report, renders, highlights.
Uses: court/calibration, vision (stubs), storage/tracks_db, analytics/report, highlights/export, video/clips, utils/io.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.utils.io import read_json, write_json
from src.utils.time import now_iso
from src.domain.models import CalibrationHomography
from src.court.calibration.artifacts import load_calibration_artifacts
from src.analytics.report import build_phase1_report
from src.highlights.export import export_highlights
from src.video.clips import probe_duration


def _meta_path(match_dir: Path) -> Path:
    return match_dir / "meta" / "meta.json"


def _report_path(match_dir: Path) -> Path:
    return match_dir / "reports" / "report.json"


def ensure_meta_and_report(match_dir: Path, video_path: Path) -> None:
    """Ensure meta/meta.json and reports/report.json exist."""
    meta_path = _meta_path(match_dir)
    report_path = _report_path(match_dir)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.exists():
        duration = probe_duration(video_path) if video_path.exists() else 0.0
        write_json(meta_path, {
            "status": "created",
            "created_at": now_iso(),
            "last_updated_at": now_iso(),
            "video_path": str(video_path),
            "video": {"duration_seconds": duration, "fps": 30},
        })
    if not report_path.exists():
        write_json(report_path, {"created_at": now_iso(), "highlights": []})


def update_meta_status(match_dir: Path, status: str) -> None:
    meta = read_json(_meta_path(match_dir))
    meta["status"] = status
    meta["last_updated_at"] = now_iso()
    write_json(_meta_path(match_dir), meta)


def stage_01_load_calibration(match_dir: Path, court_id: str, video_path: Path) -> None:
    """Load calibration from court dir or leave stub."""
    from src.pipeline.paths import court_calibration_dir
    calib_dir = court_calibration_dir(court_id)
    calib = load_calibration_artifacts(calib_dir)
    if calib:
        print(f"   ✓ Calibration loaded from court {court_id}")
    else:
        print("   (stub) No calibration yet; proceeding without court mapping.")


def stage_02_track(match_dir: Path, video_path: Path) -> None:
    """Player detection + tracking -> tracks/tracks.json (stub until vision implemented)."""
    tracks_dir = match_dir / "tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    tracks_file = tracks_dir / "tracks.json"
    if not tracks_file.exists():
        write_json(tracks_file, [])
    print("   (stub) Tracks: vision not implemented; empty tracks.json.")


def stage_03_map(match_dir: Path, court_id: str) -> None:
    """Pixel -> court mapping (stub until vision + court calibration)."""
    print("   (stub) Coordinate mapping not implemented.")


def stage_04_report(match_dir: Path, match: Dict[str, Any]) -> None:
    """Build Phase1Report -> reports/report.json."""
    meta = read_json(_meta_path(match_dir))
    video_meta = meta.get("video", {})
    tracks_path = match_dir / "tracks" / "tracks.json"
    calib_path = match_dir / "calibration" / "homography.json"
    if not calib_path.exists():
        from src.pipeline.paths import court_calibration_dir
        cal_dir = court_calibration_dir(match["court_id"])
        homography_file = cal_dir / "homography.json"
        calib_path = homography_file if homography_file.exists() else None
    report_path = build_phase1_report(
        match,
        video_meta=video_meta,
        tracks_path=tracks_path if tracks_path.exists() else None,
        calib_path=calib_path,
        out_dir=match_dir,
    )
    print(f"   ✓ Report written: {report_path}")


def stage_05_renders(match_dir: Path) -> None:
    """Render overlays (stub)."""
    (match_dir / "renders").mkdir(parents=True, exist_ok=True)
    print("   (stub) Renders not implemented.")


def stage_06_highlights(
    match_dir: Path,
    video_path: Path,
    *,
    clip_len_s: float = 12.0,
    every_s: float = 60.0,
    max_clips: int = 10,
) -> Path:
    """Export highlight clips and concat to highlights/highlights.mp4."""
    report_path = _report_path(match_dir)
    return export_highlights(
        match_dir,
        video_path,
        report_path,
        clip_len_s=clip_len_s,
        every_s=every_s,
        max_clips=max_clips,
    )
