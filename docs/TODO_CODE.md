# CourtFlow – Code improvement todo list

Prioritized list to improve the codebase. Pipeline and product shape are stable; these items add accuracy, robustness, and maintainability.

**Pre-pilot:** To max out the **pretrained** pipeline before collecting data, see **[docs/PRE_PILOT_PRETRAINED.md](PRE_PILOT_PRETRAINED.md)** (detection/tracking/ROI/ground-point tuning, no training).

---

## 1. Intelligence & accuracy (vision layer)

**Where:** `src/vision/` (see `docs/INTELLIGENCE.md`)

| Priority | Item | Notes |
|----------|------|--------|
| High | Tune or upgrade detection | In `yolo.py`: try larger model (yolov8s/m), tune `conf`/`iou`, or swap detector; keep same output contract (bbox, track_id). |
| High | Improve tracking stability | Tune ByteTrack params in `yolo.py`, or implement a different tracker in `src/vision/tracking/` and call from `pipeline.py`. |
| Medium | ROI filter tuning | In `roi_filter/filter.py`: adjust point-in-polygon (center vs bottom-center), or temporarily disable to debug. |
| Medium | Better ground point | In `ground_point.py`: move from bbox bottom-center to keypoints (e.g. ankles) when a pose model is available. |
| Low | Canonical player IDs | `vision/tracking/canonical_ids.py`: TODO – stable IDs across sessions or re-runs if needed. |

---

## 2. Ball tracking & padel analytics

**Where:** `src/vision/` (new or extend), `src/analytics/padel.py`

| Priority | Item | Notes |
|----------|------|--------|
| High | Ball detection + tracking | New pipeline (or extend vision): detect/track ball, output ball positions (and optionally shot/bounce events). |
| High | Wire ball into padel | In `padel.py`: `compute_rally_metrics`, `compute_shot_speeds`, `compute_wall_usage` are stubbed; plug in `ball_shot_frames`, `bounce_events` when ball pipeline exists. |
| Medium | Report/dashboard ball view | Optional: show ball trajectory or shot events in report/dashboard when data exists. |

---

## 3. Calibration

**Where:** `src/court/calibration/`

| Priority | Item | Notes |
|----------|------|--------|
| Medium | Calibration capture | `capture.py`: TODO – capture one or more frames to court calib dir (for manual or auto calibration). |
| Medium | Auto-fix when check fails | `auto_fix.py`: TODO – court line detection + homography fit when quick_check fails. |
| Low | Lens distortion | `distortion.py`: TODO – optional undistort before homography/ROI. |

---

## 4. Storage & pipeline data

**Where:** `src/storage/`, `src/pipeline/`

| Priority | Item | Notes |
|----------|------|--------|
| Medium | Tracks DB | `tracks_db.py`: define schema (frame, timestamp, player_id, x_pixel, y_pixel, x_court, y_court, bbox_xyxy), implement create_db, insert_tracks_batch, query; optionally wire stage 02/03 to write SQLite instead of or in addition to tracks.json. |
| Low | Detection format helpers | `vision/detection/formats.py`: TODO – convert between detector formats if you add another detector. |

---

## 5. Geometry & utils

**Where:** `src/utils/`, `src/vision/`

| Priority | Item | Notes |
|----------|------|--------|
| Low | Geometry helpers | `utils/geometry.py`: TODO – point-in-polygon, bbox overlap, apply_homography (used by vision/calibration). |

---

## 6. Cloud & API

**Where:** `src/cloud/`, `src/app/`

| Priority | Item | Notes |
|----------|------|--------|
| Low | Dashboard API | `cloud/api/dashboard_api.py`: TODO – optional FastAPI routes mirroring `src/app/api.py` for a separate dashboard service. |

---

## 7. Testing & quality

**Where:** repo root, `tests/` (to add)

| Priority | Item | Notes |
|----------|------|--------|
| High | Unit tests | Add `tests/` (or `src/.../tests`): at least for domain (models, report_contract), vision pipeline (run_tracking contract), analytics (movement, heatmap), calibration load/save. |
| Medium | Integration test | One end-to-end test: ingest + run-match on a tiny fixture video, assert tracks + report + heatmap exist and schema is valid. |
| Low | CI | Optional: GitHub Actions (or similar) to run tests and lint on push. |

---

## 8. Docs & contracts

**Where:** `docs/`, OpenAPI/schema

| Priority | Item | Notes |
|----------|------|--------|
| Low | OpenAPI / JSON Schema | Formal schema for report JSON and API responses (see `CONTRACTS_AND_STRUCTURES.md`). |
| Low | Ball pipeline in contracts | In CONTRACTS or INTELLIGENCE: add placeholder for ball_shot_frames, bounce_events so padel interfaces stay clear. |
| Low | Mermaid diagrams | Pipeline + “where data lives” diagrams in repo (e.g. in README or docs). |

---

## 9. Error handling & robustness

**Where:** pipeline stages, API, ingest

| Priority | Item | Notes |
|----------|------|--------|
| Medium | Stage timeouts | In `stages.py` / `match_runner.py`: configurable timeout for long-running stages (e.g. B5 tracking); set match state FAILED and last_error on timeout. |
| Medium | Clear failure paths | Ensure every stage writes last_error and transitions state to FAILED on error (aligned with Lab 3 interface failure modes). |
| Low | Retry for upload | In `cloud/upload.py`: retry with backoff on transient R2 errors. |

---

## Suggested order of work

1. **Tests** – Add a minimal test suite so refactors are safe.  
2. **Intelligence** – Tune detection/tracking and ROI (biggest impact on accuracy).  
3. **Ball + padel** – Ball pipeline then wire into padel analytics.  
4. **Tracks DB** – If you want queryable tracks or less JSON I/O.  
5. **Calibration** – Capture + auto-fix when you need better calibration UX.  
6. **Error handling** – Timeouts and failure paths.  
7. **Rest** – Geometry, cloud API, OpenAPI, diagrams as needed.

---

*Update this file as you complete or reprioritize items.*
