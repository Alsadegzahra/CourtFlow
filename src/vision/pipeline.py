"""
Single entry point for the "intelligence" layer: detection + tracking + ROI + ground point.
Update only this module (and the modules it uses) to improve accuracy; the rest of the pipeline
(stages 03–06, report, dashboard) stays unchanged.

Used by: pipeline/stages.py stage_02_track.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import cv2


def run_tracking(
    video_path: Path,
    court_id: str,
    match_dir: Path,
    *,
    sample_every_n_frames: int = 5,
    conf: float = 0.4,
) -> List[dict]:
    """
    Run detection + tracking on video, optional ROI filter, output track records.
    Returns list of dicts: frame, timestamp, player_id, x_pixel, y_pixel, bbox_xyxy.
    Raise or return [] on missing deps; stage_02 will write empty tracks on failure.
    """
    try:
        from src.vision.detection.yolo import _get_model, track_persons
        from src.vision.roi_filter.filter import load_roi_for_match, filter_detections_by_roi
        from src.vision.tracking.ground_point import bbox_to_ground_point
        from src.pipeline.paths import court_calibration_dir
    except ImportError:
        return []

    match_calib_dir = match_dir / "calibration"
    court_calib_dir = court_calibration_dir(court_id)
    roi_polygon = load_roi_for_match(match_calib_dir, court_calib_dir)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    model = _get_model()
    tracks: List[dict] = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        if frame_idx % sample_every_n_frames != 0:
            frame_idx += 1
            continue
        dets = track_persons(frame, model=model, conf=conf)
        if roi_polygon:
            dets = filter_detections_by_roi(dets, roi_polygon)
        for d in dets:
            track_id = d.get("track_id", -1)
            if track_id < 0:
                continue
            x, y = bbox_to_ground_point(d["bbox_xyxy"])
            tracks.append({
                "frame": frame_idx,
                "timestamp": round(frame_idx / fps, 3),
                "player_id": track_id,
                "x_pixel": round(x, 2),
                "y_pixel": round(y, 2),
                "bbox_xyxy": d["bbox_xyxy"],
            })
        frame_idx += 1
    cap.release()
    return tracks
