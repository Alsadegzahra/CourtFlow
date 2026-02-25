"""
Path conventions: where to write match outputs and court artifacts.
Uses config/settings.py (DATA_DIR, COURTS_DIR, MATCHES_DIR).
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from src.config.settings import COURTS_DIR, MATCHES_DIR

PathLike = Union[str, Path]


def match_dir(match_id: str) -> Path:
    """Canonical match output dir: data/matches/<match_id>/"""
    return MATCHES_DIR / match_id


def match_raw_dir(match_id: str) -> Path:
    """Match raw video: data/matches/<match_id>/raw/"""
    return match_dir(match_id) / "raw"


def match_tracks_dir(match_id: str) -> Path:
    """Match tracks (SQLite or JSON): data/matches/<match_id>/tracks/"""
    return match_dir(match_id) / "tracks"


def match_reports_dir(match_id: str) -> Path:
    """Match reports: data/matches/<match_id>/reports/"""
    return match_dir(match_id) / "reports"


def match_highlights_dir(match_id: str) -> Path:
    """Match highlights: data/matches/<match_id>/highlights/"""
    return match_dir(match_id) / "highlights"


def match_logs_dir(match_id: str) -> Path:
    """Match logs: data/matches/<match_id>/logs/"""
    return match_dir(match_id) / "logs"


def match_meta_path(match_id: str) -> Path:
    """Meta JSON path; kept for compatibility (meta under match dir if needed)."""
    return match_dir(match_id) / "meta" / "meta.json"


def match_report_path(match_id: str) -> Path:
    """Report JSON: data/matches/<match_id>/reports/report.json"""
    return match_reports_dir(match_id) / "report.json"


def match_tracks_db_path(match_id: str) -> Path:
    """Per-match tracks SQLite: data/matches/<match_id>/tracks/tracks.db"""
    return match_tracks_dir(match_id) / "tracks.db"


def match_tracks_json_path(match_id: str) -> Path:
    """Legacy: tracks as JSON (used until tracks_db is wired)."""
    return match_tracks_dir(match_id) / "tracks.json"


def court_dir(court_id: str) -> Path:
    """Court persistent dir: data/courts/<court_id>/"""
    return COURTS_DIR / court_id


def court_config_path(court_id: str) -> Path:
    """Court config: data/courts/<court_id>/court_config.json"""
    return court_dir(court_id) / "court_config.json"


def court_calibration_dir(court_id: str) -> Path:
    """Court calibration artifacts: data/courts/<court_id>/calibration/"""
    return court_dir(court_id) / "calibration"


def ensure_match_dirs(match_id: str) -> Path:
    """Create raw, tracks, reports, highlights, logs (and meta) for a match. Returns match dir."""
    root = match_dir(match_id)
    for sub in ("raw", "tracks", "reports", "highlights", "logs", "meta", "calibration", "renders"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
