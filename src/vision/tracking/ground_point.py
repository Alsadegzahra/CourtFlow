"""
Choose player ground point: bbox bottom-center (or ankles if pose keypoints later).
Uses: bbox geometry.
"""
from __future__ import annotations

from typing import List, Tuple


def bbox_to_ground_point(bbox_xyxy: List[float]) -> Tuple[float, float]:
    """
    (x1, y1, x2, y2) -> (center_x, y2) as pixel ground point for court mapping.
    """
    x1, y1, x2, y2 = bbox_xyxy
    return ((x1 + x2) * 0.5, float(y2))
