"""
B3: run YOLO inference (person detection) and optional tracking.
Uses: ultralytics, numpy. COCO class 0 = person.
Default: pretrained YOLO (yolo26n.pt / yolov8n.pt). For better detection use a custom-trained
model: set COURTFLOW_DETECTION_MODEL to path to your best.pt or pass detection_model to run_tracking.
Default tracker: BoT-SORT (Ultralytics). Use tracker="bytetrack.yaml" for ByteTrack.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# COCO person class id
COCO_PERSON_CLASS_ID = 0

# Pretrained model name (downloaded on first use) when no custom weights are given
DEFAULT_PRETRAINED = "yolo26n.pt"


def _resolve_model_path(value: str) -> Optional[Path]:
    """If value is a path to an existing .pt file, return it (absolute); else None."""
    p = Path(value)
    if p.suffix.lower() != ".pt":
        return None
    if p.is_absolute() and p.exists():
        return p
    # Try cwd and project root
    for base in (Path.cwd(), Path(__file__).resolve().parents[3]):
        candidate = (base / value).resolve()
        if candidate.exists():
            return candidate
    if p.exists():
        return p.resolve()
    return None


def _get_model(model_name_or_path: Optional[str] = None):
    """
    Load YOLO model for person detection.
    - If model_name_or_path is a path to an existing .pt file (or set via env COURTFLOW_DETECTION_MODEL),
      loads that custom-trained weights file (no pretrained download).
    - Otherwise uses pretrained: yolo26n.pt (falls back to yolov8n.pt if unavailable).
    """
    from ultralytics import YOLO
    value = model_name_or_path or os.getenv("COURTFLOW_DETECTION_MODEL") or DEFAULT_PRETRAINED
    path = _resolve_model_path(value)
    if path is not None:
        return YOLO(str(path))
    try:
        return YOLO(value)
    except Exception:
        if value.startswith("yolo26"):
            return YOLO("yolov8n.pt")
        raise


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
    tracker: Optional[str] = None,
) -> List[dict]:
    """
    Run detection + tracking on one frame.
    Default tracker is BoT-SORT (Ultralytics default). Pass tracker="bytetrack.yaml" for ByteTrack.
    Returns list of detections with track_id.
    Each item: {"bbox_xyxy": [x1,y1,x2,y2], "confidence": float, "class_id": int, "track_id": int}.
    """
    if model is None:
        model = _get_model()
    kwargs = dict(
        classes=[COCO_PERSON_CLASS_ID],
        conf=conf,
        iou=iou,
        persist=persist,
        verbose=False,
    )
    if tracker is not None:
        kwargs["tracker"] = tracker
    results = model.track(frame_bgr, **kwargs)
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
