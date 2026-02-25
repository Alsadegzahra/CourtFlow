"""
CourtConfig schema: rtsp_url, resolution, fps, camera_id, court dims.
Used by: video/ingest, calibration capture/check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CourtConfig:
    court_id: str
    rtsp_url: Optional[str] = None
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: int = 30
    camera_id: Optional[str] = None
    court_width_m: Optional[float] = None
    court_height_m: Optional[float] = None
    site_name: Optional[str] = None
