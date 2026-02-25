"""
Per-match automatic calibration check (light). Once per court = manual; per match = this.
Uses: court calibration artifacts, optional first frame for dimension/consistency check.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.enums import CalibrationStatus
from src.court.calibration.artifacts import load_calibration_artifacts
from src.pipeline.paths import court_calibration_dir


def run_quick_check(
    court_id: str,
    video_path: Optional[Path] = None,
    *,
    sample_frame_path: Optional[Path] = None,
) -> CalibrationStatus:
    """
    Light check: does stored calibration exist and (if we have a frame) match image size?
    Returns OK / WARN / FAIL. Per-match; keep it cheap (no heavy detection here).
    """
    calib_dir = court_calibration_dir(court_id)
    calib = load_calibration_artifacts(calib_dir)
    if not calib:
        return CalibrationStatus.FAIL

    def check_dims(w: int, h: int) -> bool:
        if w != calib.image_width or h != calib.image_height:
            return False
        return True

    # If we have a reference frame, check dimensions match (camera/resolution change?)
    if sample_frame_path is not None and sample_frame_path.exists():
        try:
            import cv2
            img = cv2.imread(str(sample_frame_path))
            if img is not None:
                h, w = img.shape[:2]
                if not check_dims(w, h):
                    return CalibrationStatus.WARN  # resolution mismatch
        except Exception:
            pass
    elif video_path is not None and video_path.exists():
        try:
            import cv2
            cap = cv2.VideoCapture(str(video_path))
            ok, img = cap.read()
            cap.release()
            if ok and img is not None:
                h, w = img.shape[:2]
                if not check_dims(w, h):
                    return CalibrationStatus.WARN
        except Exception:
            pass

    return CalibrationStatus.OK
