# Testing calibration: 12-point manual + automatic court detection

Run all commands from the **project root** (`CourtFlow-1/`). Use a match that has video at `data/matches/<match_id>/raw/match.mp4` (e.g. `match_2026_02_25_041702`).

---

## Guidelines: where to click for 12 points

The window shows the **first frame** of the video. “Top” = **far baseline** (usually where the back wall is), “bottom” = **near baseline** (closer to the camera). Click **exactly where lines meet** (corners / T-junctions).

**Court layout (bird’s-eye view; numbers = click order):**

```
        Far baseline (back)
  1 •—————————————• 2
    |             |
    |  5 •———• 6  |     ← Service line (far side): 5=left, 6=right
    |      • 12   |     ← Service T (center of that service line)
    |  |       |  |
  9 •——• 11 •——• 10    ← Net: 9=left, 11=center, 10=right
    |  |       |  |
    |  7 •———• 8  |     ← Service line (near side): 7=left, 8=right
    |             |
  4 •—————————————• 3
        Near baseline (camera side)
```

**Click order and what to aim for:**

| # | Label | Where to click |
|---|--------|----------------|
| **1** | Top-left (baseline) | Far baseline, left corner – where the left sideline meets the far baseline. |
| **2** | Top-right (baseline) | Far baseline, right corner – where the right sideline meets the far baseline. |
| **3** | Bottom-right (baseline) | Near baseline, right corner – where the right sideline meets the near baseline. |
| **4** | Bottom-left (baseline) | Near baseline, left corner – where the left sideline meets the near baseline. |
| **5** | Left service line (left) | Left sideline × **left** service line (the service line on the far side of the net from the camera). |
| **6** | Right service line (left) | Right sideline × same (left) service line. |
| **7** | Left service line (right) | Left sideline × **right** service line (the service line on the near side of the net). |
| **8** | Right service line (right) | Right sideline × right service line. |
| **9** | Left net | Where the **net** meets the **left** sideline. |
| **10** | Right net | Where the net meets the right sideline. |
| **11** | Net center | Middle of the net (center line × net). |
| **12** | Service T (center service line) | Center of either service line (the “T” where the center line meets the service line). Pick the one you see most clearly. |

**Tips:**

- Use the **first frame** as-is (or pick a frame where the court is clearly visible and use that image path).
- Prefer **line intersections**; avoid clicking on the middle of a line.
- If the net or service line is hard to see, do your best; 4 corners (1–4) are the most important – the rest improve robustness.
- **Q** or **Esc** cancels without saving.

---

## Test 1: 12-point manual calibration

**Goal:** Confirm 12-point click flow runs and produces a valid homography + ROI.

### Step 1.1 – Run 12-point calibration

```bash
python3 -m src.app.cli calibrate-court --court_id court_001 --image data/matches/match_2026_02_25_041702/raw/match.mp4 --points 12
```

- A window opens with the **first frame** of the video.
- Click **12 points in order** as in the table above (1–4 = corners, 5–8 = service line corners, 9–10 = net ends, 11 = net center, 12 = service T).
- After the 12th click the window closes and you should see:  
  `Saved manual (12-point) calibration + calib_frame + ROI for court court_001.`

**If you want to cancel:** press **Q** or **Esc** in the window.

### Step 1.2 – Check saved artifacts

```bash
ls -la data/courts/court_001/calibration/
```

You should see: `homography.json`, `calib_frame.png`, `roi_polygon.json`, `roi_mask.png`.

Optional: open `calib_frame.png` and `roi_mask.png` to confirm the court outline looks correct.

### Step 1.3 – Run pipeline with this calibration

```bash
python3 -m src.app.cli run-match --match_id match_2026_02_25_041702
```

Expect in the log:

- `[01] Load calibration` → **✓ Calibration OK for court court_001**
- Stages 02–06 run as usual (tracks, report, overlay, highlights).

Then check:

- `data/matches/match_2026_02_25_041702/reports/report.json` (has summary, players).
- `data/matches/match_2026_02_25_041702/reports/heatmap.png` (court heatmap).
- `data/matches/match_2026_02_25_041702/renders/track_overlay_preview.mp4` (overlay video).

If all of that works, **12-point manual calibration is working.**

---

## Test 2: 4-point manual calibration (sanity check)

**Goal:** Confirm 4-point mode still works.

```bash
python3 -m src.app.cli calibrate-court --court_id court_002 --image data/matches/match_2026_02_25_041702/raw/match.mp4 --points 4
```

Click only **4 corners** in order (1=top-left, 2=top-right, 3=bottom-right, 4=bottom-left). You should see:

`Saved manual (4-point) calibration + calib_frame + ROI for court court_002.`

Then run a match that uses `court_002` (or temporarily point a match to court_002) and confirm stage 01 reports calibration OK and the pipeline completes.

---

## Test 3: Automatic court detection (auto-fix / no calibration)

**Goal:** With **no** court calibration, the pipeline tries to auto-detect the court from the first frame and, if successful, saves and uses that calibration.

### Step 3.1 – Remove existing calibration for one court

Back up and remove the court calibration dir so the pipeline sees “no calibration”:

```bash
# Backup (optional)
mv data/courts/court_001/calibration data/courts/court_001/calibration.backup

# Or create a court that has no calibration yet (e.g. court_auto)
mkdir -p data/courts/court_auto
# Do NOT create data/courts/court_auto/calibration/
```

If you use a new court id (e.g. `court_auto`), you need a match that uses that court. Easiest is to **temporarily** move the calibration away for `court_001`:

```bash
mv data/courts/court_001/calibration data/courts/court_001/calibration.backup
```

### Step 3.2 – Run pipeline (no calibration)

```bash
python3 -m src.app.cli run-match --match_id match_2026_02_25_041702
```

- **If auto-detect succeeds:**  
  You should see:  
  `No calibration for this court; trying auto-detect from video...`  
  then `✓ Auto-detect applied; calibration saved.`  
  and stages 01–06 complete. New calibration is in `data/courts/court_001/calibration/` (homography.json etc.).

  **Check that the detected court is correct:**  
  Open the saved preview image:
  ```bash
  open data/courts/court_001/calibration/auto_detect_preview.png
  ```
  (On Windows: `start data/courts/court_001/calibration/auto_detect_preview.png`.)  
  The image shows the **first frame** with the **detected 4 corners** drawn as a green quad and numbered 1–4 (1=TL, 2=TR, 3=BR, 4=BL). If the quad does not align with the real court outline, use manual calibration (Test 1) instead and ignore or delete the auto-detected calibration.

- **If auto-detect fails:**  
  You see:  
  `Auto-detect failed; run manual calibration once per court.`  
  and the pipeline stops after stage 01 (no tracks/report). That’s expected when the court lines are hard to detect (angle, lighting, or no clear lines in the first frame).

### Step 3.3 – Restore manual calibration (if you backed it up)

```bash
rm -rf data/courts/court_001/calibration
mv data/courts/court_001/calibration.backup data/courts/court_001/calibration
```

---

## Test 4: Automatic check (resolution match)

**Goal:** Confirm the per-match “automatic check” runs when calibration exists.

1. Ensure `court_001` has calibration (from Test 1 or 3).
2. Run the same match again:

   ```bash
   python3 -m src.app.cli run-match --match_id match_2026_02_25_041702
   ```

3. You should see:  
   `[01] Load calibration` → **✓ Calibration OK for court court_001**  
   (no “trying auto-detect” because calibration already exists and the resolution check passes).

---

## Quick reference

| Test | What you’re checking |
|------|----------------------|
| **1** | 12-point manual calibration: click 12 points → artifacts saved → run-match uses it. |
| **2** | 4-point manual calibration still works. |
| **3** | With no calibration, pipeline tries auto-detect; if it works, calibration is saved and **auto_detect_preview.png** is written so you can verify the detected court. |
| **4** | With calibration present, per-match check runs and reports “Calibration OK”. |

**Auto-detect preview image:** When automatic court detection succeeds, open  
`data/courts/<court_id>/calibration/auto_detect_preview.png`  
to see the first frame with the detected 4 corners (green quad, labels 1–4). If the quad does not match the real court, use manual calibration instead.

If Tests 1 and 4 pass, manual calibration and the per-match check are working. If Test 3 shows “Auto-detect applied” on your video, open the preview to confirm the court is correct; if the quad is wrong or auto-detect fails, use manual calibration (Test 1) for that court.
