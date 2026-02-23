from __future__ import annotations

"""
Court calibration module.

This file defines the interface that the B4 court model team should implement:
it is responsible for estimating and loading the homography that maps image
pixels to court coordinates for a given match video.
"""

from pathlib import Path
from typing import Optional

from src.domain.models import CalibrationHomography


def estimate_court_calibration(
    video_path: Path,
    out_dir: Path,
) -> CalibrationHomography:
    """
    TODO(B4 court team): implement court detection + calibration.

    Expected behavior once implemented:
    - Run a court model on `video_path` to infer a homography from image pixels
      to court coordinates.
    - Return a `CalibrationHomography` instance describing that mapping.
    - The pipeline will persist this to `calibration/homography.json`.
    """
    raise NotImplementedError("Court calibration model is not implemented yet.")


def load_or_estimate_calibration(
    calib_path: Path,
    video_path: Path,
    out_dir: Path,
) -> CalibrationHomography:
    """
    TODO(B4 court team): decide whether to reuse an existing calibration file or recompute.

    Suggested contract:
    - If `calib_path` exists and is valid, load and return it.
    - Otherwise, call `estimate_court_calibration` and return the result.
    - The caller is responsible for saving the returned dataclass as JSON on disk.
    """
    raise NotImplementedError("Calibration loading/estimation logic is not implemented yet.")

