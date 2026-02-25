"""
A3: create ROI polygon + mask; polygon->mask helpers.
Playable court boundary in image pixels (from clicked corners or homography).
Uses: OpenCV fillPoly, utils/io
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from src.utils.io import write_json

ROI_POLYGON_FILENAME = "roi_polygon.json"
ROI_MASK_FILENAME = "roi_mask.png"


def polygon_to_mask(
    points_px: List[Tuple[float, float]],
    width: int,
    height: int,
) -> np.ndarray:
    """Render polygon as binary mask (0/255), same size as image."""
    mask = np.zeros((height, width), dtype=np.uint8)
    pts = np.array(points_px, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 255)
    return mask


def save_roi_polygon(calibration_dir: Path, points_px: List[Tuple[float, float]]) -> Path:
    """Save ROI polygon as JSON. points_px: list of [x, y] in image pixel coords."""
    calibration_dir.mkdir(parents=True, exist_ok=True)
    path = calibration_dir / ROI_POLYGON_FILENAME
    # Accept (x,y) tuples or [x,y] lists
    serializable = [[float(p[0]), float(p[1])] for p in points_px]
    payload = {"schema_version": "1", "points_px": serializable}
    write_json(path, payload)
    return path


def save_roi_mask(
    calibration_dir: Path,
    points_px: List[Tuple[float, float]],
    width: int,
    height: int,
) -> Path:
    """Render ROI polygon to a mask image and save as roi_mask.png (cached)."""
    calibration_dir.mkdir(parents=True, exist_ok=True)
    path = calibration_dir / ROI_MASK_FILENAME
    mask = polygon_to_mask(points_px, width, height)
    cv2.imwrite(str(path), mask)
    return path


def load_roi_polygon(calibration_dir: Path) -> Optional[List[Tuple[float, float]]]:
    """Load ROI polygon from JSON. Returns list of (x,y) or None if missing."""
    path = calibration_dir / ROI_POLYGON_FILENAME
    if not path.exists():
        return None
    from src.utils.io import read_json
    data = read_json(path)
    pts = data.get("points_px")
    if not pts or not isinstance(pts, list):
        return None
    return [tuple(p) for p in pts]
