"""
Build court heatmap from tracks (x_court, y_court).
Writes a PNG and returns the path. Uses numpy + OpenCV or pure numpy for 2D histogram.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


def build_heatmap(
    tracks: List[dict],
    out_path: Path,
    *,
    grid_shape: Tuple[int, int] = (50, 50),
    cmap_name: str = "hot",
    court_bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """
    Compute 2D histogram of (x_court, y_court) and save as PNG.
    grid_shape: (nx, ny) bins. court_bounds: (x_min, y_min, x_max, y_max) or auto from data.
    """
    points = []
    for t in tracks:
        x, y = t.get("x_court"), t.get("y_court")
        if x is not None and y is not None:
            points.append((float(x), float(y)))
    if not points:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Empty heatmap: small blank image
        try:
            import cv2
            blank = np.zeros((grid_shape[1], grid_shape[0], 3), dtype=np.uint8)
            blank[:] = (40, 40, 40)
            cv2.imwrite(str(out_path), blank)
        except Exception:
            pass
        return out_path

    pts = np.array(points)
    x_min, y_min = pts.min(axis=0)
    x_max, y_max = pts.max(axis=0)
    if court_bounds is not None:
        x_min, y_min, x_max, y_max = court_bounds
    # Avoid singular range
    if x_max <= x_min:
        x_max = x_min + 1.0
    if y_max <= y_min:
        y_max = y_min + 1.0

    nx, ny = grid_shape
    H, xe, ye = np.histogram2d(
        pts[:, 0], pts[:, 1],
        bins=[nx, ny],
        range=[[x_min, x_max], [y_min, y_max]],
    )
    H = H.T  # so row = y, col = x
    # Normalize to 0-255 for display
    if H.max() > 0:
        H = (H / H.max() * 255).astype(np.uint8)
    else:
        H = H.astype(np.uint8)

    # Apply colormap: hot (black -> red -> yellow -> white)
    try:
        import cv2
        if cmap_name == "hot":
            H_color = cv2.applyColorMap(H, cv2.COLORMAP_HOT)
        else:
            H_color = cv2.applyColorMap(H, cv2.COLORMAP_JET)
        # Resize for visibility (e.g. 400x400)
        h, w = H_color.shape[:2]
        scale = max(400 // w, 400 // h, 1)
        H_color = cv2.resize(H_color, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), H_color)
    except Exception:
        # Fallback: save raw grayscale
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path.with_suffix(".npy"), H)
    return out_path
