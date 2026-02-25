"""
Choose highlight windows (dummy now; smarter later from movement intensity).
Uses: analytics report or simple rules
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def select_highlights(
    report: Dict[str, Any],
    *,
    clip_len_s: float = 12.0,
    every_s: float = 60.0,
    max_clips: int = 10,
) -> List[Dict[str, Any]]:
    """Return list of {start, end, reason}. Use report['highlights'] if present else time-sampled dummy."""
    if report.get("highlights"):
        return report["highlights"]
    duration = float(report.get("summary", {}).get("match_duration_seconds") or 60.0)
    out = []
    for i in range(max_clips):
        start = i * every_s
        if start >= duration:
            break
        end = min(start + clip_len_s, duration)
        if end > start:
            out.append({"start": start, "end": end, "reason": "time_sample"})
    return out
