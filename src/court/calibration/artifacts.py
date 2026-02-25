"""
Save/load all calibration artifacts for a court (H, calib frame, ROI, undistort).
Matches flow: capture frame → (optional undistort) → manual pointing → H → ROI.
Uses: utils/io, court/calibration/homography, court/calibration/roi
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from src.domain.models import CalibrationHomography
from src.court.calibration.homography import load_homography, save_homography
from src.court.calibration.roi import save_roi_mask, save_roi_polygon

CALIB_FRAME_FILENAME = "calib_frame.jpg"


def get_homography_path(calibration_dir: Path) -> Path:
    return calibration_dir / "homography.json"


def load_calibration_artifacts(calibration_dir: Path) -> Optional[CalibrationHomography]:
    """Load homography from court calibration dir. ROI/undistort loaded separately if needed."""
    return load_homography(get_homography_path(calibration_dir))


def save_calibration_artifacts(
    calibration_dir: Path,
    calib: CalibrationHomography,
    *,
    calib_frame: Optional[np.ndarray] = None,
    roi_polygon_px: Optional[List[Tuple[float, float]]] = None,
) -> Path:
    """
    Save homography and optional calibration artifacts.
    - homography.json (always)
    - calib_frame.jpg (if calib_frame provided) – reference image from manual setup
    - roi_polygon.json + roi_mask.png (if roi_polygon_px provided) – playable court boundary
    """
    calibration_dir.mkdir(parents=True, exist_ok=True)
    path = get_homography_path(calibration_dir)
    save_homography(path, calib)

    if calib_frame is not None:
        frame_path = calibration_dir / CALIB_FRAME_FILENAME
        cv2.imwrite(str(frame_path), calib_frame)

    if roi_polygon_px is not None and len(roi_polygon_px) >= 3:
        save_roi_polygon(calibration_dir, roi_polygon_px)
        save_roi_mask(
            calibration_dir,
            roi_polygon_px,
            calib.image_width,
            calib.image_height,
        )

    return path
