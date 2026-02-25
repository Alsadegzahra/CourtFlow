"""
Draw detection/tracking overlays on frames: bboxes + player_id.
Uses: OpenCV, tracks list (frame, player_id, bbox_xyxy).
"""
from __future__ import annotations

from typing import List

import cv2
import numpy as np


def draw_tracks_on_frame(
    frame_bgr: np.ndarray,
    tracks_for_frame: List[dict],
    *,
    color: tuple = (0, 255, 0),
    thickness: int = 2,
    font_scale: float = 0.7,
) -> np.ndarray:
    """
    Draw each track's bbox and player_id on the frame. Mutates a copy and returns it.
    Each track must have 'bbox_xyxy' and 'player_id'.
    """
    out = frame_bgr.copy()
    for t in tracks_for_frame:
        bbox = t.get("bbox_xyxy")
        pid = t.get("player_id", "?")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)
        label = f"P{pid}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
        cv2.putText(
            out, label, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1,
        )
    return out


def group_tracks_by_frame(tracks: List[dict]) -> dict:
    """Return {frame_index: [track, ...]}."""
    by_frame: dict = {}
    for t in tracks:
        f = t.get("frame", 0)
        by_frame.setdefault(f, []).append(t)
    return by_frame
