"""
Manual calibration by clicking 4 or 12 court points on a reference image/frame.
4-point: corners only (top-left, top-right, bottom-right, bottom-left).
12-point: corners + service line + net (more robust homography via RANSAC).
Court space in meters; ROI uses first 4 points (court outline).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from src.domain.models import CalibrationHomography
from src.court.calibration.court_keypoints import get_court_dst, get_court_labels


def _load_frame(path: Path) -> Tuple[np.ndarray, int, int]:
    """Load image or first video frame; return (BGR image, width, height)."""
    path = Path(path)
    suf = path.suffix.lower()
    if suf in (".mp4", ".mov", ".avi", ".mkv"):
        cap = cv2.VideoCapture(str(path))
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError(f"Could not read first frame: {path}")
    else:
        frame = cv2.imread(str(path))
        if frame is None:
            raise RuntimeError(f"Could not read image: {path}")
    h, w = frame.shape[:2]
    return frame, w, h


def calibrate_from_clicks(
    image_or_video_path: Path,
    *,
    court_width_m: float = 1.0,
    court_height_m: float = 1.0,
    num_points: int = 4,
) -> Tuple[CalibrationHomography, np.ndarray, List[Tuple[int, int]]]:
    """
    Show the image/frame; user clicks 4 or 12 points in order.
    num_points=4: corners only. num_points=12: corners + service line + net (more robust).
    Returns (CalibrationHomography, reference_frame_bgr, points_px). ROI uses first 4 points.
    """
    if num_points not in (4, 12):
        raise ValueError("num_points must be 4 or 12")
    img, w, h = _load_frame(Path(image_or_video_path))
    labels = get_court_labels(num_points)
    points: List[Tuple[int, int]] = []
    display = img.copy()
    title = f"Calibration: click {num_points} court points"

    def draw_scene(d: np.ndarray, current_label_idx: int) -> None:
        """Draw court outline (closed quad 1-2-3-4) and all points; never connect 4 to 5."""
        for j, pt in enumerate(points):
            cv2.circle(d, pt, 8, (0, 255, 0), 2)
            cv2.putText(d, str(j + 1), (pt[0] + 10, pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        # Always show court outline as closed quad (1-2-3-4-1); do not draw 4->5
        if len(points) >= 4:
            quad = [points[0], points[1], points[2], points[3]]
            for k in range(4):
                cv2.line(d, quad[k], quad[(k + 1) % 4], (0, 255, 0), 2)
        cv2.putText(d, labels[current_label_idx], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(d, "Q or Esc = cancel", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)

    def on_mouse(event: int, x: int, y: int, _a: int, _b: int) -> None:
        nonlocal display
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if len(points) >= num_points:
            return
        points.append((x, y))
        display = img.copy()
        draw_scene(display, min(len(points), num_points - 1))
        cv2.imshow(title, display)

    cv2.namedWindow(title)
    cv2.setMouseCallback(title, on_mouse)

    for i in range(num_points):
        display = img.copy()
        draw_scene(display, i)
        cv2.imshow(title, display)
        while len(points) <= i:
            key = cv2.waitKey(50)
            if key == ord("q") or key == 27:
                cv2.destroyAllWindows()
                raise RuntimeError("Calibration cancelled.")
        if len(points) < num_points:
            continue

    cv2.destroyAllWindows()

    src_pts = np.array(points, dtype=np.float32)
    dst_pts = get_court_dst(num_points, court_width_m, court_height_m)
    if num_points == 4:
        H = cv2.getPerspectiveTransform(src_pts, dst_pts)
    else:
        H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if H is None:
            raise RuntimeError("findHomography failed; try re-clicking or use 4 points.")
    homography_list = H.flatten().tolist()

    calib = CalibrationHomography(
        schema_version="1",
        homography=homography_list,
        image_width=w,
        image_height=h,
        court_width_m=court_width_m,
        court_height_m=court_height_m,
    )
    # ROI = first 4 points (court outline)
    return (calib, img, points)
