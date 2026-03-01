# Court calibration: 1 per court + automatic check per match

This doc states **exactly** how we do **one calibration per court** and an **automatic check for each match**, and how that relates to the pipeline diagram (YOLO + court keypoints).

**Reference (padel / court registration):** MDPI Sensors 21(10), 3368 — *Estimating Player Positions from Padel High-Angle Videos: Accuracy Comparison of Recent Computer Vision Methods* (player position estimation; high-angle camera). Court registration in general uses point/line detection + homography; more points (e.g. 12) improve robustness (RANSAC).

---

## Goal

- **1 calibration per court:** Define the court once (geometry + play area). Stored per court; reused for every match on that court.
- **Automatic check per match:** Before processing a match, verify that the stored calibration is still valid for this video (e.g. same camera/resolution, optional geometry check). No manual re-click unless the check fails.

---

## How we do it today (Phase 1)

### 1. One calibration per court (manual, once)

| Step | What | Where / command |
|------|------|------------------|
| 1.1 | Pick a reference image or **first frame** of a video from that court. | Any frame from the same camera/angle you’ll use for matches. |
| 1.2 | Run manual calibration: click **4 or 12** court points. **4:** corners only. **12:** corners + service line + net (more robust H via RANSAC; paper/recommended). | `python3 -m src.app.cli calibrate-court --court_id court_001 --image <path> [--points 12] [--court_width_m 10 --court_height_m 20]` |
| 1.3 | Code computes homography **H** (image → court). With 12 points uses `cv2.findHomography(..., RANSAC)`. **ROI** = first 4 points (court outline). | `src/court/calibration/click_calibrate.py`, `court_keypoints.py` |
| 1.4 | Save artifacts for that court. | `src/court/calibration/artifacts.py` → `save_calibration_artifacts()` |
| 1.5 | Stored location. | `data/courts/<court_id>/calibration/`: `homography.json`, `calib_frame.png`, `roi_polygon.json`, `roi_mask.png` |

So: **one run of `calibrate-court` per court** = one calibration. No per-match action here.

---

### 2. Automatic check for each match

This runs **at the start of the pipeline** for that match (before detection/tracking).

| Step | What | Where in code |
|------|------|----------------|
| 2.1 | Load court calibration. | `stage_01_load_calibration()` in `src/pipeline/stages.py` → `load_calibration_artifacts(court_calibration_dir(court_id))`. |
| 2.2 | If no calibration exists → **FAIL.** Tell user to run manual calibration for this court; skip court mapping for this run. | Same stage; early return with message. |
| 2.3 | **Automatic check:** run a light per-match validation. | `src/court/calibration/quick_check.py` → `run_quick_check(court_id, video_path=video_path)`. |
| 2.4 | Check (current logic): (a) Calibration exists. (b) **First frame of the match video** has the **same resolution** (width × height) as the calibration reference. If (a) or (b) fails → WARN or FAIL. | Inside `run_quick_check()`: compare `calib.image_width/height` to first frame of `video_path`. |
| 2.5 | If check returns **FAIL** → try **auto-fix**: automatic court + net (line) detection from first frame → homography. | `src/court/calibration/auto_fix.py` → `try_auto_fix()` → `court_detect.estimate_homography_from_frame()` (Canny + Hough lines → intersections → 4 corners → H). |
| 2.6 | If check is **OK** (or WARN and we proceed): copy court homography into the **match** dir so tracking and mapping use it. | Stage 01 copies `homography.json` to `match_dir/calibration/`. |
| 2.7 | During tracking, **ROI** is loaded from match calib dir (or fallback court calib dir) and filters detections to “inside court” only. | `src/vision/roi_filter/filter.py` → `load_roi_for_match(match_calib_dir, court_calib_dir)`; used in `run_tracking()` in `src/vision/pipeline.py`. |

So: **every match** runs this automatic check (existence + resolution); no extra manual step unless the check fails or we add a stricter geometry check later.

---

## End-to-end flow (current)

```
Court (once per court):
  calibrate-court --court_id court_001 --image <frame>
    → data/courts/court_001/calibration/  (H, ROI, calib_frame, roi_mask)

Match (every match):
  run-match --match_id <id>
    → [01] Load calibration
          → load court calib; run_quick_check(court_id, video_path)
          → if OK: copy H to match_dir/calibration/
          → if FAIL: try auto_fix; else exit / proceed without mapping
    → [02] Track (uses ROI from court or match calib)
    → [03] Map pixels → court using H
    → [04] Report, [05] Renders, [06] Highlights
```

---

## 12 points vs 4

Using **more than 4 points** (e.g. **12**) improves homography robustness: RANSAC can reject outliers and the fit is more stable. We support:

- **4 points:** corners only; `getPerspectiveTransform`.
- **12 points:** corners + service line (4 pts) + net (3 pts) + service T (1 pt); `findHomography(..., RANSAC)`. Court model in `src/court/calibration/court_keypoints.py` (padel 10 m × 20 m, service at 6.95 m).

ROI for filtering “on court” stays the **first 4 points** (court outline) in both modes.

---

## Automatic court + net detection (point 3 / auto-fix)

We **can** do the model for automatic court + net detection and calibration:

1. **Implemented (classical):** `src/court/calibration/court_detect.py`
   - Load one frame → grayscale → Canny edges; **mask to center ROI** (ignore fence/ads at borders) and optionally **court color mask** (blue/green surface) to ignore red ads and dark structures.
   - HoughLinesP → **filter lines** (midpoint inside center ROI, min length).
   - Line-line intersections → **filter to points inside center region** → select 4 corners with **quality check** (quad centered, court-like area 5–75% of frame).
   - `findHomography(..., RANSAC)` → `CalibrationHomography`. If no quad passes quality, fallback to looser selection.
   - Wired into **auto_fix**; on success saves **auto_detect_preview.png** so you can verify. If the preview is wrong, use **manual 12-point calibration** for that court (recommended for difficult footage: pro courts with banners, glass, multiple strong edges).

2. **Optional (deep learning) later:** As in the friend’s diagram and the MDPI / court-registration literature:
   - Train or use a **court keypoint model** (e.g. YOLO with keypoint head outputting 12 court points) or **court line segmentation**.
   - Run on first frame per match → get keypoints or line mask → fit H to the 12-point (or 4-point) court model.
   - Use for “1 cal per court” (one reference frame) and “automatic check per match” (run on first frame, compare or accept H).

So: **yes**, we do automatic court + net detection for calibration: **classical pipeline now** (line detection → H), **DL model optional later** (keypoints or segmentation).

---

## Relation to your friend’s diagram (12 court keypoints)

The flowchart describes a **single model** (YOLO-style) that outputs:

- **Detection:** court (lines), players (red/blue), ball, structures.
- **Court keypoints:** 12 points (top-left, top-right, base left/right, service line points, net T, etc.) from a **keypoint/pose head**.

In that design:

- **1 calibration per court** could be: run the model once on a reference frame → get 12 court keypoints → compute homography (or store keypoints) for that court.
- **Automatic check per match:** run the same model on the **first frame** of each match → get 12 keypoints → compare to stored calibration (e.g. reprojection error) or recompute H; if consistent, use it; if not, flag or re-calibrate.

We are **not** there yet: we have no court keypoint model. Our Phase 1 is:

- **1 cal per court** = manual 4-point click → H + ROI.
- **Automatic check per match** = “does calib exist + same resolution?” (and optional later: “reproject stored points and compare to a simple detector”).

A **Phase 2** path to the diagram would be:

1. Introduce or train a model that outputs **court keypoints** (e.g. 4 corners or 12 points as in the diagram).
2. **One calibration per court:** run that model on one reference frame per court; save keypoints (or H derived from them).
3. **Automatic check per match:** run the same model on the first frame of each match; compute H (or compare keypoints); if match with stored calib, use it; else trigger re-calibration or auto-fix.

So: **same idea** (1 cal per court + automatic check per match); **today** we use manual 4-point + resolution check; **later** we can add keypoint-based calibration and a stronger per-match check.

---

## How to test (12-point + automatic detection)

See **[docs/TESTING_CALIBRATION.md](TESTING_CALIBRATION.md)** for step-by-step tests:

- **Test 1:** 12-point manual calibration → run pipeline → check report/heatmap/overlay.
- **Test 2:** 4-point manual calibration (sanity check).
- **Test 3:** Remove court calibration, run pipeline → auto-detect should try to create calibration from the first frame; restore backup if needed.
- **Test 4:** With calibration present, run pipeline → “Calibration OK” per-match check.

---

## Manual calibration first (current focus)

Automatic court detection is off for now. **Perfect manual calibration** and use it for player detection.

**With each ingested video you are asked to define court points:**

1. Ingest a video:
   ```bash
   python3 -m src.app.cli ingest-match --court_id court_001 --input /path/to/video.mp4
   ```
2. When ingest finishes you see: **`Define court points for this court now? [y/N]:`**
3. Type **y** and press Enter → a window opens with the **first frame** of the ingested video. Click **12 points** in order (or 4 if you passed `--calibrate_points 4`). See [Guidelines: where to click](TESTING_CALIBRATION.md#guidelines-where-to-click-for-12-points).
4. Calibration is saved for that court; later matches on the same court reuse it (same resolution) until you run calibrate-court again.

To calibrate **without** re-ingesting (e.g. for an existing match):
```bash
python3 -m src.app.cli calibrate-court --court_id court_001 --image data/matches/<match_id>/raw/match.mp4 --points 12
```

---

## What to do next (concrete)

1. **Run one calibration per court**
   For each court (e.g. `court_001`), run ingest and answer **y** when asked to define court points, or run:
   ```bash
   python3 -m src.app.cli calibrate-court --court_id court_001 --image data/matches/match_2026_02_25_041702/raw/match.mp4 --court_width_m 10 --court_height_m 20 --points 12
   ```
   Click 4 or 12 points in order. That’s the “1 calibration per court.”

2. **Automatic check is already there**  
   Every `run-match` runs `stage_01` → `run_quick_check(court_id, video_path)`. So “automatic check for each match” is: **exists + same resolution**. No extra step for you.

3. **Optional improvements**
   - **Frame choice:** Add a way to calibrate from a specific frame index (e.g. middle of video) instead of always the first.
   - **Stronger check:** Later, add a check that uses the first frame (e.g. reproject 4 corners with H and validate with edge/corner or a small net).
   - **Auto-fix:** Implement `try_auto_fix()` (e.g. line detection + fit H) when the check fails.
   - **Phase 2:** Add court keypoint model and switch to keypoint-based calibration and per-match keypoint check as in the diagram.

---

## Summary

| | Phase 1 (now) | Phase 2 (diagram-style, later) |
|--|----------------|--------------------------------|
| **1 calibration per court** | Manual 4-point click; save H + ROI in `data/courts/<court_id>/calibration/`. | Run court keypoint model on one reference frame; save keypoints or H. |
| **Automatic check per match** | At pipeline start: load calib → `run_quick_check()` (exists + same resolution) → copy H to match dir; ROI filters detections. | Run keypoint model on first frame; compare/recompute H; accept or re-calibrate. |

We do **1 calibration per court** with the CLI and **automatic check per match** inside `stage_01` + `quick_check`; the diagram shows the target end-state when we add court keypoint detection.
