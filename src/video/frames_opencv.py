"""
Frame iterator for a video file using cv2.VideoCapture.
Uses: OpenCV
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple, Optional

import cv2
import numpy as np


def iter_frames(
    video_path: Path,
    *,
    max_frames: Optional[int] = None,
) -> Iterator[Tuple[int, float, np.ndarray]]:
    """Yield (frame_index, timestamp_sec, frame_bgr)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")
    fps = max(float(cap.get(cv2.CAP_PROP_FPS)), 1e-6)
    idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield idx, idx / fps, frame
            idx += 1
            if max_frames is not None and idx >= max_frames:
                break
    finally:
        cap.release()
