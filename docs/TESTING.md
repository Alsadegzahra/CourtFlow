# How to test so far

Run these from the **project root** (`CourtFlow-1/`). Use `python3 -m` so the same Python and paths are used everywhere.

---

## 1. Pipeline (ingest → run-match)

**If you don’t have a match yet:**

```bash
# Ingest a video (creates a new match, copies to data/matches/<match_id>/raw/match.mp4)
python3 -m src.app.cli ingest-match --court_id court_001 --input sample_videos/sample.mp4
# Note the match_id printed (e.g. match_2026_02_25_123456)
```

**Run the full pipeline** (report + highlights):

```bash
# Use your match_id, or omit to use the latest FINALIZED match
python3 -m src.app.cli run-match --match_id match_2026_02_25_022906
```

**Stage 02 (tracking)** requires `ultralytics` for YOLO person detection + ByteTrack. Install with:  
`pip install ultralytics`  
If not installed, stage 02 writes empty tracks and the pipeline continues.

You should see:

- `[01] Load calibration` → “No calibration for this court” or “✓ Calibration OK”
- `[02] Player detection + tracking` → “✓ Tracked N points from M frames (K players)” or “(skip) Vision deps missing”
- `[03]` … `[06]` → “✓ Report written”, “✓ Highlights”
- `data/matches/<match_id>/tracks/tracks.json`, `reports/report.json`, `highlights/highlights.mp4`

---

## 2. Calibration flow (stage 01)

**Without any court calibration:**

```bash
python3 -m src.app.cli run-match --match_id match_2026_02_25_022906
```

Expect: `No calibration for this court; run manual calibration once per court.`

**With manual calibration** you can either **click 4 court corners** (true manual) or use **identity** from video size:

**Option A – Manual (click 4 corners)**  
A window opens with the first frame; click in order: 1) top-left court corner, 2) top-right, 3) bottom-right, 4) bottom-left. Press Q or Esc to cancel.

```bash
python3 -m src.app.cli calibrate-court --court_id court_001 --image data/matches/match_2026_02_25_022906/raw/match.mp4
```

Optionally set court size in meters (default 1×1):  
`python3 -m src.app.cli calibrate-court --court_id court_001 --image path/to/frame.jpg --court_width_m 10.97 --court_height_m 23.77`

**Option B – Identity from video** (no clicks):

```bash
python3 -m src.app.cli calibrate-court --court_id court_001 --identity --image data/matches/match_2026_02_25_022906/raw/match.mp4
```

Either option creates `data/courts/court_001/calibration/homography.json`. For identity, it looks like (replace width/height with your video frame size if different):

```json
{
  "schema_version": "1",
  "homography": [1,0,0, 0,1,0, 0,0,1],
  "image_width": 1920,
  "image_height": 1080
}
```

Then run again:

```bash
python3 -m src.app.cli run-match --match_id match_2026_02_25_022906
```

Expect: `✓ Calibration OK for court court_001` and `match_dir/calibration/homography.json` to appear. If your video has different dimensions you’ll see `⚠ Calibration warn` and it will still copy.

---

## 3. API and user dashboard

**Start the API:**

```bash
python3 -m uvicorn src.app.api:app --reload
```

Then in the browser:

- **Main page:** http://127.0.0.1:8000/
- **View a match:** http://127.0.0.1:8000/view?match_id=match_2026_02_25_022906
- **API docs:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health

---

## 4. Ops dashboard (Streamlit)

In a **second terminal**:

```bash
python3 -m streamlit run dashboard/app.py
```

Open the URL (e.g. http://localhost:8501), pick a match or enter Court ID + Match ID, click “View dashboard”. You should see report, highlights, cloud section.

---

## 5. Cloud upload (optional)

If `.env` has R2 credentials:

```bash
python3 -m src.app.cli upload-match --match_id match_2026_02_25_022906
```

Expect: `Uploaded keys: ['matches/.../highlights.mp4', 'matches/.../report.json']`.

---

## Quick checklist

| Test | Command / action |
|------|-------------------|
| Ingest | `ingest-match --court_id court_001 --input sample_videos/sample.mp4` |
| Run pipeline | `run-match` or `run-match --match_id <id>` |
| Calibration (no calib) | `run-match` → “No calibration for this court” |
| Calibration (click 4 corners) | `calibrate-court --court_id court_001 --image <image_or_video>` → click 4 corners in window |
| Calibration (identity) | `calibrate-court --court_id court_001 --identity --image <path>` |
| Calibration (with homography.json) | Add court_001/calibration/homography.json, then `run-match` → “✓ Calibration OK” |
| API | `uvicorn src.app.api:app --reload` → open `/` and `/view?match_id=...` |
| Streamlit | `streamlit run dashboard/app.py` |
| R2 upload | `upload-match --match_id <id>` |
