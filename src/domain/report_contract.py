"""
Phase 1 report and tracks contract helpers.
Keep this stable; analytics fills metrics, pipeline/dashboard consume.
"""
from __future__ import annotations

from typing import Any, Dict, List

from src.domain.models import Phase1Report, TrackRecord, Tracks, new_phase1_report


def empty_tracks() -> Tracks:
    return []


def empty_report(match_id: str, court_id: str, video_meta: Dict[str, Any]) -> Dict[str, Any]:
    report = new_phase1_report(match_id=match_id, court_id=court_id, video_meta=video_meta)
    return {
        "schema_version": report.schema_version,
        "match_id": report.match_id,
        "court_id": report.court_id,
        "generated_at": report.generated_at.isoformat(timespec="seconds"),
        "video": report.video,
        "summary": report.summary,
        "players": report.players,
        "team": report.team,
        "renders": report.renders,
        "highlights": [{"start": h.start, "end": h.end, "reason": h.reason} for h in report.highlights],
        "status": report.status,
    }
