# Pre-pilot: perfect the pretrained pipeline

**Goal:** Get the best possible results from **pretrained** models and tuning **before** the pilot. No training, no fine-tuning, no need for our own dataset yet. Once this is solid, run the pilot, collect data, then fine-tune (and optionally train) later.

**Order:**  
1. **Perfect pretrained** (this doc) → 2. **Pilot** (collect data) → 3. **Fine-tune** (using pilot data) → 4. **Optionally train** (e.g. ball, custom classes).

**Current focus (Feb 2026):** Court calibration first. Test run showed 4 real players but 53–71 unique track IDs (ID switches). Best run so far: `--sample_every 3` (53 IDs). After calibration and ROI are solid, revisit tracking/detection tuning.

---

## Checklist: pretrained-only improvements

Everything below uses only pretrained models, config, or code changes. No data collection or training.

### Detection (`src/vision/detection/yolo.py`)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Model choice | Default is `yolo26n.pt`. Try `yolo26s.pt` or `yolo26m.pt` (better accuracy, more compute) and pick the best trade-off for your hardware. |
| ☐ | Confidence threshold | Tune `conf` (e.g. 0.3–0.5). Lower = more detections, more false positives; higher = fewer misses, may drop distant players. |
| ☐ | IoU threshold | Tune `iou` for NMS (e.g. 0.45–0.6). Affects overlapping detections. |

### Tracking (`src/vision/detection/yolo.py` + Ultralytics)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Tracker choice | Default is BoT-SORT. Try `tracker="bytetrack.yaml"` (pass to `track_persons(..., tracker="bytetrack.yaml")` from pipeline) and compare ID stability. |
| ☐ | Tracker params | Copy `ultralytics/cfg/trackers/bytetrack.yaml` or `botsort.yaml` to the repo, tweak `track_high_thresh`, `track_low_thresh`, `track_buffer`, `match_thresh`; pass path to `track_persons(..., tracker="path/to/custom.yaml")`. |
| ☐ | ReID (BoT-SORT) | If using BoT-SORT, try `with_reid: True` in tracker YAML for better identity across occlusions (adds compute). |

### ROI (`src/vision/roi_filter/filter.py`)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Point for “on court” | Already uses bottom-center. Optionally try bbox center in `filter_detections_by_roi` (e.g. `use_bottom_center=False` and add center logic) if players at the net get dropped. |
| ☐ | Disable ROI for debug | In `run_tracking`, temporarily skip ROI (or pass empty polygon) to see if ROI is cutting valid players; then tighten polygon or fix calibration. |

### Ground point (`src/vision/tracking/ground_point.py`)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Keep bottom-center | Already default; no change if it’s good enough. |
| ☐ | Optional: pretrained pose | If you add a **pretrained** pose model (e.g. YOLO pose `yolo26n-pose.pt`), use ankle/keypoint as ground point instead of bbox bottom-center for better court position. Still no training. |

### Pipeline (`src/vision/pipeline.py`)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Sample rate | Tune `sample_every_n_frames` (e.g. 3, 5, 10). Lower = more points, more compute; higher = faster, may miss fast moves. |
| ☑ | Pass tracker to run_tracking | `run_tracking(..., iou=0.5, tracker=None)` and `stage_02_track(..., iou=..., tracker=...)`; CLI: `run-match --tracker bytetrack.yaml --iou 0.45 --conf 0.35 --sample_every 3`. |

### Calibration (no ML) — **do this next**

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | 4-point quality | Ensure court corners are clicked consistently; re-run calibration on a few frames to see if homography is stable. |
| ☐ | ROI polygon | Ensure ROI polygon matches the play area (not too tight; no extra regions). |
| ☐ | Calibration flow | Use `calibrate-court` (and capture/artifacts) so court + ROI are correct before more tracking runs. |

### Validation (no new data)

| Done? | Item | What to do |
|-------|------|------------|
| ☐ | Visual check | Run pipeline on 1–2 test videos; inspect overlay (renders) and heatmap. Do tracks follow players? Are IDs stable? |
| ☐ | Report sanity | Check report.json: num_players, total_distance, per-player stats. Do they match what you see in the video? |

---

## Out of scope for “perfect pretrained”

- **Training or fine-tuning** – needs data; do after pilot.
- **Ball detection** – needs new model/data; Phase 2.
- **Custom-trained pose/court** – needs data; after pilot.
- **New datasets** – not needed for pretrained tuning.

---

## After this checklist

When the pretrained pipeline is as good as you can get it:

1. **Pilot** – Run on real matches; collect video (and optionally export tracks/reports for analysis).
2. **Collect data** – Keep footage and any labels you add (e.g. “ball here”) for future fine-tuning.
3. **Fine-tune** – Use pilot data to fine-tune person (or train ball) when ready.
4. **Optionally train** – Custom models (e.g. ball, stroke type) as needed.
