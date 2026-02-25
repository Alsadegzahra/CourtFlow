"""
Save/load all calibration artifacts for a court (H, ROI, undistort).
Uses: utils/io, court/calibration/homography
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.models import CalibrationHomography
from src.court.calibration.homography import load_homography, save_homography


def get_homography_path(calibration_dir: Path) -> Path:
    return calibration_dir / "homography.json"


def load_calibration_artifacts(calibration_dir: Path) -> Optional[CalibrationHomography]:
    """Load homography from court calibration dir. ROI/undistort TBD."""
    return load_homography(get_homography_path(calibration_dir))


def save_calibration_artifacts(calibration_dir: Path, calib: CalibrationHomography) -> Path:
    """Save homography to court calibration dir."""
    calibration_dir.mkdir(parents=True, exist_ok=True)
    path = get_homography_path(calibration_dir)
    save_homography(path, calib)
    return path
