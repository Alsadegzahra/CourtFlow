from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


# ---- Core DB-style entities -------------------------------------------------


@dataclass
class Court:
    court_id: str
    site_name: Optional[str]
    created_at: datetime
    updated_at: datetime


MatchState = Literal[
    "CREATED",
    "RECORDING",
    "FINALIZING",
    "FINALIZED",
    "PROCESSING",
    "DONE",
    "FAILED",
]


@dataclass
class Match:
    match_id: str
    court_id: str
    source_type: Literal["FILE", "RTSP"]
    source_uri: str
    output_dir: str
    state: MatchState
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class Artifact:
    id: int
    match_id: str
    type: str          # e.g. RAW_CHUNK, RAW_MERGED, HIGHLIGHTS_MP4
    path: str
    status: str        # WRITING, READY, FAILED
    size_bytes: Optional[int]
    created_at: datetime
    updated_at: datetime


# ---- Tracks + calibration ----------------------------------------------------


@dataclass
class TrackRecord:
    frame: int
    timestamp: float
    player_id: int
    bbox_xyxy: Optional[List[float]]  # [x1, y1, x2, y2]
    x_pixel: float
    y_pixel: float
    x_court: Optional[float]
    y_court: Optional[float]


Tracks = List[TrackRecord]


@dataclass
class CalibrationHomography:
    """
    Contract for calibration/homography.json.
    homography is a 3x3 matrix stored row-major as 9 floats.
    """

    schema_version: str
    homography: List[float]  # len == 9
    image_width: int
    image_height: int
    court_width_m: Optional[float] = None
    court_height_m: Optional[float] = None


# ---- Highlights + report -----------------------------------------------------


@dataclass
class HighlightSegment:
    start: float
    end: float
    reason: str


@dataclass
class Phase1Report:
    """
    Contract for reports/report.json used in Phase 1.
    """

    schema_version: str
    match_id: str
    court_id: str
    generated_at: datetime
    video: Dict[str, Any]
    summary: Dict[str, Any]
    players: Dict[str, Any] = field(default_factory=dict)
    team: Dict[str, Any] = field(default_factory=dict)
    renders: Dict[str, Any] = field(default_factory=dict)
    highlights: List[HighlightSegment] = field(default_factory=list)
    status: str = "placeholder"


def new_phase1_report(
    match_id: str,
    court_id: str,
    video_meta: Dict[str, Any],
) -> Phase1Report:
    """
    Helper factory mirroring the existing empty_report(...) shape.
    """
    duration = float(video_meta.get("duration_seconds") or 0.0)

    return Phase1Report(
        schema_version="phase1_v1",
        match_id=match_id,
        court_id=court_id,
        generated_at=datetime.now().replace(microsecond=0),
        video=video_meta,
        summary={"match_duration_seconds": duration},
    )

