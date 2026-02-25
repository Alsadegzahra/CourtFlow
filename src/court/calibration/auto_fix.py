"""
Optional automatic calibration fix when quick_check fails. Tries to re-detect court and compute H.
If it fails or is uncertain, caller should fall back to manual calibration.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.domain.models import CalibrationHomography


def try_auto_fix(
    court_id: str,
    video_path: Path,
    *,
    frame_index: int = 0,
) -> Optional[CalibrationHomography]:
    """
    Try to recover calibration from a frame (e.g. court line detection -> homography).
    Returns new CalibrationHomography if successful, else None → caller should prompt for manual.
    """
    # TODO: run court line detection on frame, fit homography to court model, return new calib
    return None
