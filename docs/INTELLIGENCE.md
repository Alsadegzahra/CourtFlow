
# Intelligence layer – where to improve accuracy

The **pipeline** (ingest → track → map → report → renders → highlights) is fixed. The only part you need to change for better accuracy is the **intelligence** layer: detection and tracking.

---

## Single entry point

- **`src/vision/pipeline.py`** → **`run_tracking(video_path, court_id, match_dir, ...)`**
- Stage 02 calls this and writes whatever it returns to `tracks/tracks.json`. The rest of the app (mapping, report, heatmap, highlights, dashboard) only reads `tracks.json` and does not care how it was produced.

**So:** improve or replace the implementation behind `run_tracking`; leave the pipeline and the rest of the codebase as-is.

---

## What lives inside the intelligence layer

| Piece | Module | Role |
|-------|--------|------|
| **Entry point** | `src/vision/pipeline.py` | `run_tracking()` – video → list of track records. |
| **Detection** | `src/vision/detection/yolo.py` | Person detection (default: pretrained YOLO26n/YOLOv8n). Use a **custom-trained** `.pt` via `--detection-model` or env `COURTFLOW_DETECTION_MODEL` – see [DETECTION_TRAINING.md](DETECTION_TRAINING.md). |
| **Tracking** | Same (ByteTrack via ultralytics) or `src/vision/tracking/` | Stable IDs over time. Replace with a better tracker if needed. |
| **ROI filter** | `src/vision/roi_filter/filter.py` | Keep only detections inside court polygon. Tune or disable here. |
| **Ground point** | `src/vision/tracking/ground_point.py` | Bbox → (x, y) for court mapping. Use bottom-center or keypoints later. |

---

## Contract: what `run_tracking` must return

Each item in the list must be a dict with at least:

- `frame` (int)
- `timestamp` (float)
- `player_id` (int, stable across frames)
- `x_pixel`, `y_pixel` (float, ground point in image)
- `bbox_xyxy` (list of 4 floats, optional but used by overlays)

Stage 03 adds `x_court`, `y_court` from calibration. Downstream code only expects these fields.

---

## How to improve accuracy (without touching the pipeline)

1. **Better detection**
   - **Use a trained model instead of pretrained:** set `COURTFLOW_DETECTION_MODEL` to your `best.pt` path, or pass `--detection-model path/to/best.pt` to `run-match`. See [DETECTION_TRAINING.md](DETECTION_TRAINING.md) for how to train YOLO on your data.
   - In `src/vision/detection/yolo.py`: default is pretrained `yolo26n.pt` / `yolov8n.pt`. You can also try larger pretrained variants by setting the env to `yolo26s.pt` or `yolov8m.pt`, or tune `conf` / `iou`; or replace with another detector that returns the same format (list of dicts with `bbox_xyxy`, `track_id`).

2. **Better tracking**
   - Option A: keep using `track_persons()` in yolo.py but tune ultralytics tracker params.
   - Option B: implement a different tracker in `src/vision/tracking/` and call it from `vision/pipeline.py` instead of `track_persons` (e.g. detect per frame, then run your tracker on the detections).

3. **ROI**
   - In `src/vision/roi_filter/filter.py`: adjust how the polygon is used (e.g. center vs bottom-center), or temporarily disable ROI in `run_tracking` to see if it helps.

4. **Ground point**
   - In `src/vision/tracking/ground_point.py`: switch from bbox bottom-center to keypoints (e.g. ankles) when you have a pose model.

5. **End-to-end swap**
   - Replace the body of `run_tracking()` in `src/vision/pipeline.py` with a completely different implementation (e.g. another library or service) as long as the returned list of dicts matches the contract above.

---

## Summary

- **One place to update:** `src/vision/` (and mainly `pipeline.py` + the modules it uses).
- **Pipeline unchanged:** stages 03–06, report, heatmap, highlights, and the website only consume `tracks.json`.
- **Contract:** each track record has `frame`, `timestamp`, `player_id`, `x_pixel`, `y_pixel`, and optionally `bbox_xyxy`.

Improve detection/tracking in that layer; the rest keeps working.
