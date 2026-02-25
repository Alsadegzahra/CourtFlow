"""
Timestamps, formatting, fps helpers.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow_iso(timespec: str = "seconds") -> str:
    return datetime.now(timezone.utc).isoformat(timespec=timespec)


def now_iso(timespec: str = "seconds") -> str:
    return datetime.now().isoformat(timespec=timespec)
