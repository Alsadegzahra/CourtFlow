"""
Automatic court (and net) line detection for calibration.
Classical pipeline: Canny edges -> Hough lines -> line intersections -> fit homography.
Used by auto_fix when quick_check fails; can also be used for "automatic check" per match.
Reference: MDPI Sensors 21(10) 3368 (padel position estimation); court registration via
points + lines (e.g. PnLCalib). For better robustness (occlusion, lighting), a deep
learning model (court keypoints or line segmentation) can be added later.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from src.config.constants import COURT_HEIGHT_M, COURT_WIDTH_M
from src.domain.models import CalibrationHomography
from src.court.calibration.court_keypoints import court_4_dst


def _load_frame(video_path: Path, frame_index: int = 0) -> Optional[np.ndarray]:
    """Load one frame; support image or video."""
    path = Path(video_path)
    if path.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv"):
        cap = cv2.VideoCapture(str(path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        cap.release()
        return frame if ok and frame is not None else None
    img = cv2.imread(str(path))
    return img


def _court_roi_mask(h: int, w: int, margin_frac: float = 0.12) -> np.ndarray:
    """1 inside center ROI (court likely here), 0 in borders (ads, fence, walls)."""
    x0, x1 = int(w * margin_frac), int(w * (1 - margin_frac))
    y0, y1 = int(h * margin_frac), int(h * (1 - margin_frac))
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[y0:y1, x0:x1] = 1
    return mask


def _court_color_mask(bgr: np.ndarray) -> np.ndarray:
    """Mask where court surface is likely (blue/green hue). Helps ignore red ads, dark fence."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    # Blue court: H ~100-130; green court: H ~35-85. Broad range to be safe.
    blue_green = ((h >= 35) & (h <= 130)) | ((h >= 80) & (h <= 140))
    ok_sv = (s >= 25) & (v >= 40)
    mask = np.uint8(np.where(blue_green & ok_sv, 1, 0))
    return mask


def _edges(gray: np.ndarray, blur_ksize: int = 5, low: int = 50, high: int = 150) -> np.ndarray:
    """Canny edges after Gaussian blur."""
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    return cv2.Canny(blurred, low, high)


def _lines_from_edges(edge: np.ndarray) -> np.ndarray:
    """HoughLinesP; return (N, 4) x1,y1,x2,y2."""
    lines = cv2.HoughLinesP(
        edge,
        rho=1,
        theta=np.pi / 180,
        threshold=40,
        minLineLength=40,
        maxLineGap=15,
    )
    if lines is None or len(lines) == 0:
        return np.array([]).reshape(0, 4)
    return lines.reshape(-1, 4)


def _filter_lines_roi(lines: np.ndarray, w: int, h: int, margin_frac: float = 0.12) -> np.ndarray:
    """Keep lines whose midpoint lies inside the center ROI and length >= min_len."""
    x0, x1 = w * margin_frac, w * (1 - margin_frac)
    y0, y1 = h * margin_frac, h * (1 - margin_frac)
    min_len = min(60, min(w, h) * 0.08)
    out = []
    for line in lines:
        x1_, y1_, x2_, y2_ = line
        mx = (x1_ + x2_) / 2
        my = (y1_ + y2_) / 2
        if not (x0 <= mx <= x1 and y0 <= my <= y1):
            continue
        length = np.hypot(x2_ - x1_, y2_ - y1_)
        if length >= min_len:
            out.append(line)
    return np.array(out, dtype=np.float32).reshape(-1, 4) if out else np.array([]).reshape(0, 4)


def _filter_intersections_roi(pts: np.ndarray, w: int, h: int, margin_frac: float = 0.15) -> np.ndarray:
    """Keep intersections that lie inside the center region (court area)."""
    x0, x1 = w * margin_frac, w * (1 - margin_frac)
    y0, y1 = h * margin_frac, h * (1 - margin_frac)
    inside = (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
    return pts[inside]


def _line_intersection(
    x1: float, y1: float, x2: float, y2: float,
    x3: float, y3: float, x4: float, y4: float,
) -> Optional[Tuple[float, float]]:
    """Intersection of two segments (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4)."""
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-10:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return (px, py)
    return None


def _intersections_from_lines(lines: np.ndarray, min_angle_deg: float = 15.0) -> np.ndarray:
    """Compute pairwise line intersections; filter by angle to avoid near-parallel."""
    points: List[Tuple[float, float]] = []
    n = len(lines)
    for i in range(n):
        x1, y1, x2, y2 = lines[i]
        v1 = np.array([x2 - x1, y2 - y1], dtype=float)
        norm1 = np.linalg.norm(v1)
        if norm1 < 1e-6:
            continue
        for j in range(i + 1, n):
            x3, y3, x4, y4 = lines[j]
            v2 = np.array([x4 - x3, y4 - y3], dtype=float)
            norm2 = np.linalg.norm(v2)
            if norm2 < 1e-6:
                continue
            cos_angle = np.abs(np.dot(v1, v2) / (norm1 * norm2))
            if cos_angle > np.cos(np.radians(min_angle_deg)):
                continue
            pt = _line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
            if pt is not None:
                points.append(pt)
    if not points:
        return np.array([]).reshape(0, 2)
    return np.array(points, dtype=np.float32)


def _quad_quality(ordered: np.ndarray, w: int, h: int) -> float:
    """Higher = better. Prefer quad centered in image with reasonable area (court-sized)."""
    if len(ordered) != 4:
        return -1.0
    cx = np.mean(ordered[:, 0])
    cy = np.mean(ordered[:, 1])
    # Prefer centroid near image center
    center_score = 1.0 - (abs(cx - w / 2) / (w / 2) + abs(cy - h / 2) / (h / 2)) / 2
    area = cv2.contourArea(ordered.astype(np.float32).reshape(-1, 1, 2))
    img_area = w * h
    area_frac = area / img_area
    # Court usually 10-55% of frame
    if area_frac < 0.05 or area_frac > 0.75:
        return -1.0
    area_score = 1.0 - abs(area_frac - 0.25) / 0.25
    return center_score * 0.6 + area_score * 0.4


def _order_corners_quad(pts: np.ndarray, w: int, h: int) -> Optional[np.ndarray]:
    """
    From a set of 2D points, select 4 that form a convex quad and order as
    top-left, top-right, bottom-right, bottom-left (in image: top = small y).
    Prefer quads that are centered and have court-like area. pts: (N, 2). Returns (4, 2) or None.
    """
    if len(pts) < 4:
        return None
    pts_f = pts.astype(np.float32)
    hull = cv2.convexHull(pts_f)
    hull = hull.reshape(-1, 2)
    if len(hull) < 4:
        idx0 = np.argmin(pts[:, 0] + pts[:, 1])
        idx1 = np.argmax(pts[:, 1] - pts[:, 0])
        idx2 = np.argmax(pts[:, 0] + pts[:, 1])
        idx3 = np.argmin(pts[:, 1] - pts[:, 0])
        four = np.array([pts[idx0], pts[idx1], pts[idx2], pts[idx3]], dtype=np.float32)
    else:
        n = len(hull)
        cent = np.mean(hull, axis=0)
        angles = np.arctan2(hull[:, 1] - cent[1], hull[:, 0] - cent[0])
        order = np.argsort(angles)
        hull = hull[order]
        if n > 4:
            step = max(1, n // 4)
            four = np.array([hull[0], hull[min(step, n - 1)], hull[min(2 * step, n - 1)], hull[min(3 * step, n - 1)]], dtype=np.float32)
        else:
            four = hull[:4].astype(np.float32)
    tl = np.argmin(four[:, 0] + four[:, 1])
    ordered = np.roll(four, -tl, axis=0)
    if ordered[1, 0] < ordered[0, 0]:
        ordered = ordered[[0, 3, 2, 1]]
    ordered = np.array(ordered, dtype=np.float32)
    if _quad_quality(ordered, w, h) < 0:
        return None
    return ordered


def estimate_homography_from_frame(
    video_path: Path,
    frame_index: int = 0,
    *,
    court_width_m: float = COURT_WIDTH_M,
    court_height_m: float = COURT_HEIGHT_M,
    return_preview: bool = True,
    use_color_mask: bool = True,
) -> Tuple[Optional[CalibrationHomography], Optional[np.ndarray]]:
    """
    Automatic court detection from one frame: edges (masked to center + court color) ->
    lines -> intersections -> 4 corners (quality check) -> H.
    Returns (CalibrationHomography, preview_bgr) if successful, else (None, None).
    use_color_mask: restrict edges to blue/green court surface to ignore red ads, dark fence.
    """
    frame = _load_frame(video_path, frame_index)
    if frame is None:
        return (None, None)
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edge = _edges(gray)
    # Restrict to center ROI (ignore fence, ads, walls at frame borders)
    center_mask = _court_roi_mask(h, w, margin_frac=0.12)
    edge = cv2.bitwise_and(edge, edge, mask=center_mask)
    if use_color_mask:
        color_mask = _court_color_mask(frame)
        color_mask = cv2.dilate(color_mask, np.ones((5, 5), np.uint8))
        edge = cv2.bitwise_and(edge, edge, mask=color_mask)
    edge = cv2.dilate(edge, np.ones((3, 3), np.uint8))
    lines = _lines_from_edges(edge)
    lines = _filter_lines_roi(lines, w, h, margin_frac=0.12)
    if len(lines) < 6:
        # Fallback: no color mask, looser ROI
        edge = _edges(gray)
        edge = cv2.bitwise_and(edge, edge, mask=_court_roi_mask(h, w, margin_frac=0.08))
        edge = cv2.dilate(edge, np.ones((3, 3), np.uint8))
        lines = _lines_from_edges(edge)
        lines = _filter_lines_roi(lines, w, h, margin_frac=0.08)
    if len(lines) < 6:
        return (None, None)
    pts = _intersections_from_lines(lines)
    pts = _filter_intersections_roi(pts, w, h, margin_frac=0.15)
    if len(pts) < 4:
        pts = _intersections_from_lines(lines)
        pts = _filter_intersections_roi(pts, w, h, margin_frac=0.08)
    if len(pts) < 4:
        return (None, None)
    ordered = _order_corners_quad(pts, w, h)
    if ordered is None:
        # Retry with looser area check: allow any convex quad in center
        ordered = _order_corners_quad_loose(pts, w, h)
    if ordered is None:
        return (None, None)
    dst = court_4_dst(court_width_m, court_height_m)
    H, mask = cv2.findHomography(ordered, dst, cv2.RANSAC, 5.0)
    if H is None or mask is None or np.sum(mask) < 3:
        return (None, None)
    calib = CalibrationHomography(
        schema_version="1",
        homography=H.flatten().tolist(),
        image_width=w,
        image_height=h,
        court_width_m=court_width_m,
        court_height_m=court_height_m,
    )
    preview = None
    if return_preview:
        preview = frame.copy()
        quad = ordered.astype(np.int32)
        cv2.polylines(preview, [quad], isClosed=True, color=(0, 255, 0), thickness=2)
        for i, pt in enumerate(quad):
            cv2.circle(preview, tuple(pt), 8, (0, 255, 0), 2)
            cv2.putText(
                preview, str(i + 1), (pt[0] + 10, pt[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1,
            )
        cv2.putText(
            preview, "Auto-detected court (1=TL 2=TR 3=BR 4=BL)",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1,
        )
    return (calib, preview)


def _order_corners_quad_loose(pts: np.ndarray, w: int, h: int) -> Optional[np.ndarray]:
    """Like _order_corners_quad but skip quality check (use when strict check rejects all)."""
    if len(pts) < 4:
        return None
    pts_f = pts.astype(np.float32)
    hull = cv2.convexHull(pts_f)
    hull = hull.reshape(-1, 2)
    if len(hull) < 4:
        idx0 = np.argmin(pts[:, 0] + pts[:, 1])
        idx1 = np.argmax(pts[:, 1] - pts[:, 0])
        idx2 = np.argmax(pts[:, 0] + pts[:, 1])
        idx3 = np.argmin(pts[:, 1] - pts[:, 0])
        four = np.array([pts[idx0], pts[idx1], pts[idx2], pts[idx3]], dtype=np.float32)
    else:
        n = len(hull)
        cent = np.mean(hull, axis=0)
        angles = np.arctan2(hull[:, 1] - cent[1], hull[:, 0] - cent[0])
        order = np.argsort(angles)
        hull = hull[order]
        if n > 4:
            step = max(1, n // 4)
            four = np.array([hull[0], hull[min(step, n - 1)], hull[min(2 * step, n - 1)], hull[min(3 * step, n - 1)]], dtype=np.float32)
        else:
            four = hull[:4].astype(np.float32)
    tl = np.argmin(four[:, 0] + four[:, 1])
    ordered = np.roll(four, -tl, axis=0)
    if ordered[1, 0] < ordered[0, 0]:
        ordered = ordered[[0, 3, 2, 1]]
    return np.array(ordered, dtype=np.float32)
