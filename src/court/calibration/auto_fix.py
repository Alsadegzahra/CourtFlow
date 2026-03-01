"""
Optional automatic calibration fix when quick_check fails. Tries to re-detect court and compute H.
Uses court_detect (Canny + Hough lines -> intersections -> 4 corners -> homography).
If it fails or is uncertain, caller should fall back to manual calibration.
Saves auto_detect_preview.png when successful so you can check if the detected court is correct.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2

from src.domain.models import CalibrationHomography
from src.court.calibration.court_detect import estimate_homography_from_frame
from src.pipeline.paths import court_calibration_dir

AUTO_DETECT_PREVIEW_FILENAME = "auto_detect_preview.png"


def try_auto_fix(
    court_id: str,
    video_path: Path,
    *,
    frame_index: int = 0,
) -> Optional[CalibrationHomography]:
    """
    Try to recover calibration from a frame (court line detection -> homography).
    When successful, saves a preview image to calibration_dir/auto_detect_preview.png
    so you can verify the detected court quad. Returns new CalibrationHomography if
    successful, else None → caller should prompt for manual.
    """
    calib, preview = estimate_homography_from_frame(video_path, frame_index=frame_index)
    if calib is None:
        return None
    calib_dir = court_calibration_dir(court_id)
    calib_dir.mkdir(parents=True, exist_ok=True)
    if preview is not None:
        preview_path = calib_dir / AUTO_DETECT_PREVIEW_FILENAME
        cv2.imwrite(str(preview_path), preview)
    return calib
