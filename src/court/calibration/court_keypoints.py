"""
Padel court keypoint model: world coordinates (meters) for 4 or 12 points.
Used for homography estimation (more points = more robust with findHomography + RANSAC).
Reference: standard padel 10m x 20m; service line 6.95 m from each baseline; net at 10 m.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from src.config.constants import COURT_HEIGHT_M, COURT_WIDTH_M

# Service line distance from baseline (m) – ITF padel
SERVICE_LINE_FROM_BASELINE_M = 6.95
NET_MID_Y = COURT_HEIGHT_M / 2.0  # 10 m
SERVICE_LEFT_Y = SERVICE_LINE_FROM_BASELINE_M  # 6.95
SERVICE_RIGHT_Y = COURT_HEIGHT_M - SERVICE_LINE_FROM_BASELINE_M  # 13.05
COURT_CENTER_X = COURT_WIDTH_M / 2.0  # 5 m

# Labels for UI (order must match COURT_12_DST)
COURT_4_LABELS = [
    "1. Top-left (baseline)",
    "2. Top-right (baseline)",
    "3. Bottom-right (baseline)",
    "4. Bottom-left (baseline)",
]

COURT_12_LABELS = [
    "1. Top-left (baseline)",
    "2. Top-right (baseline)",
    "3. Bottom-right (baseline)",
    "4. Bottom-left (baseline)",
    "5. Left service line (left)",
    "6. Right service line (left)",
    "7. Left service line (right)",
    "8. Right service line (right)",
    "9. Left net",
    "10. Right net",
    "11. Net center",
    "12. Service T (center service line)",
]

# 4 corners: top-left, top-right, bottom-right, bottom-left (same as before)
def court_4_dst(
    court_width_m: float = COURT_WIDTH_M,
    court_height_m: float = COURT_HEIGHT_M,
) -> np.ndarray:
    """Destination points in court space (meters) for 4-point homography."""
    return np.array(
        [
            [0, 0],
            [court_width_m, 0],
            [court_width_m, court_height_m],
            [0, court_height_m],
        ],
        dtype=np.float32,
    )


# 12 points: 4 corners + service line corners + net ends + net center + service T
def court_12_dst(
    court_width_m: float = COURT_WIDTH_M,
    court_height_m: float = COURT_HEIGHT_M,
) -> np.ndarray:
    """Destination points in court space (meters) for 12-point homography.
    Order: 4 corners, 4 service-line corners, left net, right net, net center, service T."""
    sl = SERVICE_LINE_FROM_BASELINE_M
    sr = court_height_m - sl
    cx = court_width_m / 2.0
    mid = court_height_m / 2.0
    return np.array(
        [
            [0, 0],           # 1 top-left baseline
            [court_width_m, 0],  # 2 top-right baseline
            [court_width_m, court_height_m],  # 3 bottom-right baseline
            [0, court_height_m],  # 4 bottom-left baseline
            [0, sl],          # 5 left service (left side)
            [court_width_m, sl],  # 6 right service (left side)
            [0, sr],          # 7 left service (right side)
            [court_width_m, sr],  # 8 right service (right side)
            [0, mid],         # 9 left net
            [court_width_m, mid],  # 10 right net
            [cx, mid],        # 11 net center
            [cx, sl],         # 12 service T
        ],
        dtype=np.float32,
    )


def get_court_dst(
    num_points: int,
    court_width_m: float = COURT_WIDTH_M,
    court_height_m: float = COURT_HEIGHT_M,
) -> np.ndarray:
    """Get destination points for 4 or 12 points."""
    if num_points == 4:
        return court_4_dst(court_width_m, court_height_m)
    if num_points == 12:
        return court_12_dst(court_width_m, court_height_m)
    raise ValueError("num_points must be 4 or 12")


def get_court_labels(num_points: int) -> List[str]:
    """Labels for click UI."""
    if num_points == 4:
        return COURT_4_LABELS
    if num_points == 12:
        return COURT_12_LABELS
    raise ValueError("num_points must be 4 or 12")
