"""
B4: remove detections outside ROI polygon/mask.
Uses: OpenCV pointPolygonTest, court calibration artifacts.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


def _bbox_bottom_center(bbox_xyxy: List[float]) -> Tuple[float, float]:
    """(x1, y1, x2, y2) -> (center_x, y2) as ground point."""
    from src.vision.tracking.ground_point import bbox_to_ground_point
    return bbox_to_ground_point(bbox_xyxy)


def point_in_polygon(
    x: float, y: float,
    points_px: List[Tuple[float, float]],
) -> bool:
    """True if (x,y) is inside the polygon (or on boundary)."""
    if len(points_px) < 3:
        return False
    contour = np.array(points_px, dtype=np.float32).reshape((-1, 1, 2))
    result = cv2.pointPolygonTest(contour, (x, y), False)
    return result >= 0


def filter_detections_by_roi(
    detections: List[dict],
    roi_polygon_px: List[Tuple[float, float]],
    *,
    use_bottom_center: bool = True,
) -> List[dict]:
    """
    Keep only detections whose ground point (bottom-center of bbox) lies inside the ROI polygon.
    Each detection must have "bbox_xyxy" key.
    """
    if not roi_polygon_px or len(roi_polygon_px) < 3:
        return detections
    out = []
    for d in detections:
        bbox = d.get("bbox_xyxy")
        if not bbox or len(bbox) != 4:
            continue
        x, y = _bbox_bottom_center(bbox)
        if point_in_polygon(x, y, roi_polygon_px):
            out.append(d)
    return out


def load_roi_for_match(
    match_calib_dir: Path,
    court_calib_dir: Optional[Path] = None,
) -> Optional[List[Tuple[float, float]]]:
    """
    Load ROI polygon from match calibration dir, or fallback to court calibration dir.
    Returns points_px or None if no ROI found.
    """
    from src.court.calibration.roi import load_roi_polygon
    poly = load_roi_polygon(match_calib_dir)
    if poly is not None:
        return poly
    if court_calib_dir is not None:
        return load_roi_polygon(court_calib_dir)
    return None
