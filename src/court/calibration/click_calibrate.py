"""
Manual calibration by clicking 4 court corners on a reference image/frame.
Order: 1=top-left, 2=top-right, 3=bottom-right, 4=bottom-left (of the court in the image).
Court space is normalized 0–1 (optional court_width_m / court_height_m for real meters later).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from src.domain.models import CalibrationHomography


# Order of clicks: top-left, top-right, bottom-right, bottom-left (court rectangle in image)
LABELS = ["1. Top-left court corner", "2. Top-right court corner", "3. Bottom-right court corner", "4. Bottom-left court corner"]

# Court corner order: top-left, top-right, bottom-right, bottom-left
# Default 1m x 1m; use court_width_m / court_height_m for real dimensions
def _court_dst(court_width_m: float, court_height_m: float) -> np.ndarray:
    return np.array(
        [[0, 0], [court_width_m, 0], [court_width_m, court_height_m], [0, court_height_m]],
        dtype=np.float32,
    )


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
) -> Tuple[CalibrationHomography, np.ndarray, List[Tuple[int, int]]]:
    """
    Show the image/frame; user clicks 4 points in order (top-left, top-right, bottom-right, bottom-left).
    Returns (CalibrationHomography, reference_frame_bgr, points_px) for saving calib_frame + ROI.
    """
    img, w, h = _load_frame(Path(image_or_video_path))
    points: List[Tuple[int, int]] = []
    display = img.copy()

    def on_mouse(event: int, x: int, y: int, _a: int, _b: int) -> None:
        nonlocal display
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if len(points) >= 4:
            return
        points.append((x, y))
        cv2.circle(display, (x, y), 8, (0, 255, 0), 2)
        if len(points) <= 3:
            cv2.line(display, points[-1], points[-1], (0, 255, 0), 2)
        if len(points) >= 2:
            cv2.line(display, points[-2], points[-1], (0, 255, 0), 2)
        if len(points) == 4:
            cv2.line(display, points[3], points[0], (0, 255, 0), 2)
        cv2.imshow("Calibration: click 4 court corners", display)

    cv2.namedWindow("Calibration: click 4 court corners")
    cv2.setMouseCallback("Calibration: click 4 court corners", on_mouse)

    for i in range(4):
        display = img.copy()
        for j, pt in enumerate(points):
            cv2.circle(display, pt, 8, (0, 255, 0), 2)
            if j > 0:
                cv2.line(display, points[j - 1], pt, (0, 255, 0), 2)
        if len(points) == 4:
            cv2.line(display, points[3], points[0], (0, 255, 0), 2)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(display, LABELS[i], (10, 30), font, 0.7, (0, 255, 255), 2)
        cv2.putText(display, "Q or Esc = cancel", (10, 60), font, 0.5, (128, 128, 128), 1)
        cv2.imshow("Calibration: click 4 court corners", display)
        while len(points) <= i:
            key = cv2.waitKey(50)
            if key == ord("q") or key == 27:
                cv2.destroyAllWindows()
                raise RuntimeError("Calibration cancelled.")
        if len(points) < 4:
            continue

    cv2.destroyAllWindows()

    src_pts = np.array(points, dtype=np.float32)
    dst_pts = _court_dst(court_width_m, court_height_m)
    H = cv2.getPerspectiveTransform(src_pts, dst_pts)
    homography_list = H.flatten().tolist()

    calib = CalibrationHomography(
        schema_version="1",
        homography=homography_list,
        image_width=w,
        image_height=h,
        court_width_m=court_width_m,
        court_height_m=court_height_m,
    )
    return (calib, img, points)
