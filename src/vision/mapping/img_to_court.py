"""
B7: apply homography to ground points -> (x_court, y_court).
Uses: OpenCV/numpy, court calibration H
"""
from __future__ import annotations

from typing import List, Tuple, Optional
from src.domain.models import CalibrationHomography

# TODO: apply H to (x_pixel, y_pixel) -> (x_court, y_court)
