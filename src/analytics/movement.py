"""
Distances/speeds/coverage from tracks (list of dicts with timestamp, player_id, x_court, y_court).
Uses: tracks JSON or list of track dicts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _get_court_point(t: dict) -> Optional[Tuple[float, float]]:
    x = t.get("x_court")
    y = t.get("y_court")
    if x is None or y is None:
        return None
    return (float(x), float(y))


def compute_movement_metrics(
    tracks: List[dict],
    *,
    court_scale_to_meters: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute per-player and aggregate movement from tracks.
    Tracks must have: player_id, timestamp, x_court, y_court.
    Returns:
      summary: total_distance, total_duration_s, num_players, total_track_points
      players: { str(player_id): { distance, duration_s, avg_speed, point_count } }
    Court coordinates are in calibration units; if court_scale_to_meters is set (e.g. court
    width in meters for normalized 0–1), distances are scaled to meters.
    """
    if not tracks:
        return {
            "summary": {
                "total_distance": 0.0,
                "total_duration_s": 0.0,
                "num_players": 0,
                "total_track_points": 0,
            },
            "players": {},
        }

    scale = court_scale_to_meters if court_scale_to_meters is not None else 1.0

    by_player: Dict[int, List[dict]] = {}
    for t in tracks:
        pid = t.get("player_id")
        if pid is None:
            continue
        pt = _get_court_point(t)
        if pt is None:
            continue
        by_player.setdefault(int(pid), []).append(t)

    players_out: Dict[str, Any] = {}
    total_distance = 0.0
    total_duration = 0.0
    total_points = len(tracks)

    for pid, list_t in by_player.items():
        # Sort by timestamp
        list_t = sorted(list_t, key=lambda x: (x.get("timestamp") or 0))
        if len(list_t) < 2:
            players_out[str(pid)] = {
                "distance": 0.0,
                "duration_s": 0.0,
                "avg_speed": 0.0,
                "point_count": len(list_t),
            }
            continue
        duration_s = (list_t[-1].get("timestamp") or 0) - (list_t[0].get("timestamp") or 0)
        if duration_s <= 0:
            duration_s = 0.0
            dist = 0.0
        else:
            dist = 0.0
            for i in range(1, len(list_t)):
                p0 = _get_court_point(list_t[i - 1])
                p1 = _get_court_point(list_t[i])
                if p0 and p1:
                    dist += ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
            dist *= scale
        avg_speed = (dist / duration_s) if duration_s > 0 else 0.0
        players_out[str(pid)] = {
            "distance": round(dist, 2),
            "duration_s": round(duration_s, 2),
            "avg_speed": round(avg_speed, 4),
            "point_count": len(list_t),
        }
        total_distance += dist
        if duration_s > total_duration:
            total_duration = duration_s

    return {
        "summary": {
            "total_distance": round(total_distance, 2),
            "total_duration_s": round(total_duration, 2),
            "num_players": len(by_player),
            "total_track_points": total_points,
        },
        "players": players_out,
    }
