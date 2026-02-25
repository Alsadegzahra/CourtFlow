# Court calibration flow

Calibration is **manual once per court**, then a **light automatic check per match**. If the check fails, we either **try an automatic fix** or **fall back to manual** calibration.

---

## Overall flow

```
┌─────────────────────────────────────────────────────────────────┐
│  ONCE PER COURT                                                  │
│  Manual calibration → save H to data/courts/<court_id>/calibration/  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  PER MATCH (stage 01)                                            │
│  Load stored calibration → run light automatic check             │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                 [ OK ]         [ WARN ]         [ FAIL ]
                    │               │               │
                    │               │               ▼
                    │               │      ┌────────────────────┐
                    │               │      │ Try auto-fix       │
                    │               │      │ (detection → new H)│
                    │               │      └────────────────────┘
                    │               │               │
                    │               │      ┌────────┴────────┐
                    │               │      ▼                 ▼
                    │               │   [ success ]      [ fail ]
                    │               │      │                 │
                    │               │      │                 ▼
                    │               │      │         Manual calibration
                    ▼               ▼      ▼                 or run without
              Use calibration for this match (copy to match dir)   court mapping
```

---

## Manual setup flow (first calibration)

The first-time calibration matches this pipeline:

1. **Capture calibration frame** – Use an image or the first frame of a video (`--image <path>`).
2. **(Optional) Lens undistort** – Not implemented yet; stub in `court/calibration/distortion.py`. When needed, we’ll compute undistort maps and use an undistorted frame for the next steps.
3. **Manual court pointing** – Click 4 court corners in order (top-left, top-right, bottom-right, bottom-left). These give image points + court coordinates.
4. **Compute homography** – **H** (image → court) is computed from the 4 point pairs and saved as `homography.json`.
5. **Define court ROI** – The same 4 corners define the playable court boundary in the image. We save `roi_polygon.json` (polygon in pixel coords) and `roi_mask.png` (cached mask).

**Persistent artifacts** under `data/courts/<court_id>/calibration/`:

| Artifact | Description |
|----------|-------------|
| `calib_frame.jpg` | Reference image used for clicking (from click calibration only). |
| `homography.json` | **H** image → court (`H_img_to_court`). |
| `roi_polygon.json` | Playable court boundary as polygon in image pixels (from click calibration only). |
| `roi_mask.png` | Optional cached mask of the court ROI (from click calibration only). |
| `undistort_maps.npz` | Optional; not yet implemented (lens correction). |

**Used by:** Player tracking can use `roi_polygon` / `roi_mask` to ignore detections outside the court; coordinate conversion uses `homography`.

---

## Steps in detail

### 1. Manual calibration (once per court)

- Someone runs the **manual calibration** for that court:
  - **Click 4 court corners (true manual):**  
    `python3 -m src.app.cli calibrate-court --court_id <id> --image <path>`  
    Opens a window with the image or first video frame; you click in order: top-left, top-right, bottom-right, bottom-left court corner. **H** is computed from these 4 point correspondences. Optional: `--court_width_m` and `--court_height_m` (default 1×1 m).
  - **Identity from image/video:**  
    `python3 -m src.app.cli calibrate-court --court_id <id> --identity --image <path>`  
    Writes an identity homography using the image/video frame size (no point selection).
  - **Copy existing homography:**  
    `python3 -m src.app.cli calibrate-court --court_id <id> --homography_file <path to homography.json>`
- **H** is saved under `data/courts/<court_id>/calibration/homography.json`. When you use **click** calibration, we also save `calib_frame.jpg`, `roi_polygon.json`, and `roi_mask.png`.
- Automatic detection is **not** required here; this is the source of truth.

### 2. Per-match automatic check (light)

- Before using calibration for a match, the pipeline runs a **quick check** (see `src/court/calibration/quick_check.py`).
- The check is **light**: e.g. calibration exists, and (if we have a frame) image dimensions match the ones stored with **H** (so we catch resolution/camera changes).
- Result: **OK**, **WARN**, or **FAIL**.

### 3. If OK or WARN

- Stored calibration is **copied into the match dir** (`match_dir/calibration/homography.json`).
- Downstream stages (mapping, report) use it for that match.

### 4. If FAIL

- Pipeline calls **auto-fix** (see `src/court/calibration/auto_fix.py`): try to re-detect court and compute a new **H** from the match video.
- **If auto-fix succeeds**: new **H** is saved to the court calibration dir and used for this match (and future matches until the next fail).
- **If auto-fix fails**: pipeline proceeds **without** court mapping for this match and logs that **manual calibration** (or manual re-run after fixing) is needed.

### 5. Manual again when needed

- When the check fails and auto-fix cannot recover, ops must run **manual calibration** again for that court (or fix camera/setup and re-run).
- After manual calibration is re-done, the next match will use the new **H** and the per-match check will validate it again.

---

## Where it lives in code

| Step | Module / stage |
|------|-----------------|
| Manual calibration (compute & save H) | CLI `calibrate-court` + `court/calibration/click_calibrate.py` (click 4 corners) or `--identity` / `--homography_file` → `save_calibration_artifacts` |
| Load stored H | `court/calibration/artifacts.py`, `homography.py` |
| Per-match check | `court/calibration/quick_check.py` → `run_quick_check(court_id, video_path)` |
| Auto-fix (stub) | `court/calibration/auto_fix.py` → `try_auto_fix(court_id, video_path)` |
| Wire into pipeline | `pipeline/stages.py` → `stage_01_load_calibration` |

---

## Summary

- **Manual once per court** → store **H** in court dir.
- **Automatic check per match** → light (existence + optional dimension check).
- **If check fails** → try **automatic fix**; if that fails → **manual** (or proceed without court mapping for that match).
