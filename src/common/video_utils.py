import math
from pathlib import Path
from typing import Dict, Any

import cv2

from src.common.ffmpeg_utils import probe_duration_ffprobe


def get_video_metadata(video_path: Path) -> Dict[str, Any]:
    """
    Extract basic video metadata.

    Uses:
      - OpenCV for fps, frame count, resolution
      - ffprobe for accurate duration
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    cap.release()

    # Use ffprobe for accurate duration
    try:
        duration_seconds = probe_duration_ffprobe(video_path)
    except Exception:
        # fallback to OpenCV estimate
        duration_seconds = 0.0
        if fps > 0 and frame_count > 0:
            duration_seconds = frame_count / fps

    return {
        "fps": fps,
        "frame_count": frame_count,
        "duration_seconds": duration_seconds,
        "width": width,
        "height": height,
    }


def frame_to_time(frame_index: int, fps: float) -> float:
    """
    Convert frame index -> time in seconds.
    """
    if fps <= 0:
        return 0.0
    return frame_index / fps


def time_to_frame(seconds: float, fps: float) -> int:
    """
    Convert time in seconds -> nearest frame index.
    """
    if fps <= 0:
        return 0
    return int(math.floor(seconds * fps))