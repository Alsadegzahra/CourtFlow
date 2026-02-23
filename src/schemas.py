from __future__ import annotations

from typing import Any, Dict, List

from src.domain.models import (
    TrackRecord,
    Tracks,
    Phase1Report,
    new_phase1_report,
)

def empty_tracks() -> Tracks:
    """
    Phase 1 Tracks Contract (per detection/track per frame).
    See `src.domain.models.TrackRecord` for the exact field contract.
    """
    return []


def empty_report(match_id: str, court_id: str, video_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1 Report Contract (one report per match).
 
    Keep this stable. R (Analytics) fills metrics. Z (System) reads it for dashboard/export.
    Backed by the `Phase1Report` dataclass in `src.domain.models`.
    """
    report: Phase1Report = new_phase1_report(match_id=match_id, court_id=court_id, video_meta=video_meta)
    # Persisted JSON shape stays as a plain dict.
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
        "highlights": [
            {"start": h.start, "end": h.end, "reason": h.reason}
            for h in report.highlights
        ],
        "status": report.status,
    }
