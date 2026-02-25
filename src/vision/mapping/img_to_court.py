"""
Apply homography H to map pixel (ground) points to court coordinates.
Uses: court calibration H (3x3 row-major).
"""
from __future__ import annotations

from typing import List, Tuple, Optional

from src.domain.models import CalibrationHomography


def pixel_to_court(
    x_pixel: float,
    y_pixel: float,
    calib: CalibrationHomography,
) -> Tuple[float, float]:
    """
    Map one point from image (pixel) to court space using the 3x3 homography.
    Returns (x_court, y_court). Scale depends on how H was built (e.g. normalized 0–1 or meters).
    """
    H = calib.homography
    if len(H) != 9:
        raise ValueError("Homography must have 9 elements (3x3 row-major)")
    # [x', y', w'] = H @ [x, y, 1]
    xp = H[0] * x_pixel + H[1] * y_pixel + H[2]
    yp = H[3] * x_pixel + H[4] * y_pixel + H[5]
    wp = H[6] * x_pixel + H[7] * y_pixel + H[8]
    if abs(wp) < 1e-9:
        return (0.0, 0.0)
    return (xp / wp, yp / wp)


def apply_calibration_to_tracks(
    tracks: List[dict],
    calib: CalibrationHomography,
    *,
    x_key: str = "x_pixel",
    y_key: str = "y_pixel",
    out_x_key: str = "x_court",
    out_y_key: str = "y_court",
) -> List[dict]:
    """
    In-place (mutates) each track: set x_court, y_court from x_pixel, y_pixel using calib.
    Returns the same list.
    """
    for t in tracks:
        x = t.get(x_key)
        y = t.get(y_key)
        if x is not None and y is not None:
            xc, yc = pixel_to_court(float(x), float(y), calib)
            t[out_x_key] = xc
            t[out_y_key] = yc
    return tracks
