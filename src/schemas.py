from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def empty_tracks() -> List[Dict[str, Any]]:
    """
    Phase 1 Tracks Contract (per detection/track per frame):

    Each element should look like:
      {
        "frame": int,
        "timestamp": float,
        "player_id": int,
        "bbox_xyxy": [x1, y1, x2, y2],         # optional but recommended
        "x_pixel": float, "y_pixel": float,    # representative point in image
        "x_court": float | None,
        "y_court": float | None
      }

    Notes:
    - player_id is ONLY within-match identity (temporary track id).
    - x_court/y_court can be None until court calibration is available.
    """
    return []


def empty_report(match_id: str, court_id: str, video_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1 Report Contract (one report per match).

    Keep this stable. R (Analytics) fills metrics. Z (System) reads it for dashboard/export.
    """
    duration = float(video_meta.get("duration_seconds") or 0.0)

    return {
        "schema_version": "phase1_v1",
        "match_id": match_id,
        "court_id": court_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "video": video_meta,
        "summary": {
            "match_duration_seconds": duration,
        },
        "players": {
            # keys are stringified player IDs: "0", "1", "2", "3"
            # values filled by analytics
        },
        "team": {
            # e.g. spacing stats, team-level metrics
        },
        "renders": {
            # file paths created by Z (optional)
            # "heatmap_player_0": "renders/heatmap_player_0.png"
        },
        "highlights": [
            # list of segments:
            # {"start": 120.5, "end": 128.2, "reason": "high_intensity"}
        ],
        "status": "placeholder"
    }
