"""
B3: run YOLO inference (person detection) and optional tracking (ByteTrack).
Uses: ultralytics, numpy. COCO class 0 = person.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# COCO person class id
COCO_PERSON_CLASS_ID = 0


def _get_model(model_name: str = "yolov8n.pt"):
    """Load YOLO model (downloads on first use)."""
    from ultralytics import YOLO
    return YOLO(model_name)


def detect_persons(
    frame_bgr: np.ndarray,
    model=None,
    *,
    conf: float = 0.4,
    iou: float = 0.5,
) -> List[dict]:
    """
    Run person detection on one frame. Returns list of detections.
    Each detection: {"bbox_xyxy": [x1,y1,x2,y2], "confidence": float, "class_id": int}.
    """
    if model is None:
        model = _get_model()
    results = model.predict(
        frame_bgr,
        classes=[COCO_PERSON_CLASS_ID],
        conf=conf,
        iou=iou,
        verbose=False,
    )
    out = []
    for r in results:
        if r.boxes is None:
            continue
        for i in range(len(r.boxes)):
            xyxy = r.boxes.xyxy[i].cpu().numpy().tolist()
            conf_val = float(r.boxes.conf[i].cpu().numpy())
            cls_id = int(r.boxes.cls[i].cpu().numpy())
            out.append({
                "bbox_xyxy": [float(x) for x in xyxy],
                "confidence": conf_val,
                "class_id": cls_id,
            })
    return out


def track_persons(
    frame_bgr: np.ndarray,
    model=None,
    *,
    conf: float = 0.4,
    iou: float = 0.5,
    persist: bool = True,
) -> List[dict]:
    """
    Run detection + tracking (ByteTrack) on one frame.
    Returns list of detections with track_id.
    Each item: {"bbox_xyxy": [x1,y1,x2,y2], "confidence": float, "class_id": int, "track_id": int}.
    """
    if model is None:
        model = _get_model()
    results = model.track(
        frame_bgr,
        classes=[COCO_PERSON_CLASS_ID],
        conf=conf,
        iou=iou,
        persist=persist,
        verbose=False,
    )
    out = []
    for r in results:
        if r.boxes is None:
            continue
        track_ids = r.boxes.id
        for i in range(len(r.boxes)):
            xyxy = r.boxes.xyxy[i].cpu().numpy().tolist()
            conf_val = float(r.boxes.conf[i].cpu().numpy())
            cls_id = int(r.boxes.cls[i].cpu().numpy())
            tid = int(track_ids[i].cpu().numpy()) if track_ids is not None else -1
            out.append({
                "bbox_xyxy": [float(x) for x in xyxy],
                "confidence": conf_val,
                "class_id": cls_id,
                "track_id": tid,
            })
    return out
