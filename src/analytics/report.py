"""
Build Phase1Report (small JSON) from metrics + metadata.
Uses: analytics/movement, utils/io, domain/models, domain/report_contract
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.models import Phase1Report
from src.domain.report_contract import empty_report
from src.utils.io import write_json_atomic


def build_phase1_report(
    match: dict,
    *,
    video_meta: dict,
    tracks_path: Optional[Path] = None,
    calib_path: Optional[Path] = None,
    out_dir: Path,
) -> Path:
    """Build report.json for a match. Placeholder until movement metrics are implemented."""
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
