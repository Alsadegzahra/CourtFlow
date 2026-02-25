"""
A2: compute/load homography H_img_to_court from clicked points or detection.
Uses: OpenCV, utils/geometry, utils/io
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.models import CalibrationHomography
from src.utils.io import read_json


def load_homography(path: Path) -> Optional[CalibrationHomography]:
    """Load homography from JSON. Returns None if file missing."""
    if not path.exists():
        return None
    data = read_json(path)
    return CalibrationHomography(**data)


def save_homography(path: Path, calib: CalibrationHomography) -> None:
    """Save homography to JSON."""
    from src.utils.io import ensure_dir, write_json
    ensure_dir(path.parent)
    write_json(path, {
        "schema_version": calib.schema_version,
        "homography": calib.homography,
        "image_width": calib.image_width,
        "image_height": calib.image_height,
        "court_width_m": calib.court_width_m,
        "court_height_m": calib.court_height_m,
    })
