## CourtFlow – Phase 1 Skeleton

CourtFlow is an MVP system for turning raw match video into structured
analytics and highlight videos. This repo uses a **unified structure**:
`src/app` (CLI + API), `src/pipeline` (match_runner + stages), `src/court`,
`src/video`, `src/vision`, `src/storage`, `src/analytics`, `src/highlights`,
`src/cloud`, `src/domain`, `src/config`, `src/utils`. Data lives under
`data/courts/` and `data/matches/`.

---

### What’s working now

- **End-to-end pipeline**: Ingest video → run match (stages 01–06) → report + highlights. Match state and artifacts stored in SQLite.
- **CLI**: `calibrate-court` (stub), `ingest-match`, `run-match`, `daily-check`, `upload-match` (R2).
- **API (FastAPI)**: Health, list/get matches, match report, meta, artifacts, cloud upload and presigned URLs. Serves user dashboard at `/view`.
- **User dashboard (Phase 1)**: Single URL `/view?match_id=xxx` — AI Movement Intelligence report (match structure, positional, physical load) and highlights. Shareable link; no login.
- **Ops dashboard (Streamlit)**: Full internal view — Court ID + Match ID or list, source video, meta, tracks, report, highlights, cloud upload, artifacts.
- **Cloud (R2)**: Upload highlights + report to Cloudflare R2; presigned links for viewing. Env-based config via `.env`.

### Tools used

| Layer | Tools |
|-------|------|
| **Language & runtime** | Python 3 (3.9+; 3.10+ recommended) |
| **API** | FastAPI, Uvicorn |
| **Ops dashboard** | Streamlit |
| **User UI** | Single HTML page (`dashboard/view.html`) + Fetch API (no framework) |
| **DB** | SQLite (match registry, artifacts) |
| **Video** | OpenCV (headless), FFmpeg / ffprobe (ingest, clips, concat) |
| **Cloud storage** | Cloudflare R2 (S3-compatible, boto3) |
| **Config** | `python-dotenv` (`.env`), `src/config/settings.py` |

---

### How to run

1. **Calibrate court** (stub for now):  
   `python -m src.app.cli calibrate-court --court_id court_001`

2. **Ingest a match** (create match + copy/re-encode to `data/matches/<id>/raw/match.mp4`):  
   `python -m src.app.cli ingest-match --court_id court_001 --input /path/to/video.mp4`

3. **Process the match** (run pipeline → report + highlights):  
   `python -m src.app.cli run-match`  
   (uses latest FINALIZED match) or  
   `python -m src.app.cli run-match --match_id match_2026_02_24_01`

4. **Optional: process all FINALIZED matches**:  
   `python -m src.app.cli daily-check`

5. **API**:  
   `python3 -m uvicorn src.app.api:app --reload`  
   Then open http://127.0.0.1:8000/docs in your browser for Swagger.

6. **Ops dashboard (Streamlit)**:  
   `python3 -m streamlit run dashboard/app.py`  
   Use **Court ID** (optional) + **Match ID** and click **View dashboard**, or pick from the list.

7. **User dashboard (link UI)** – with the API running, open in a browser:  
   `http://127.0.0.1:8000/view?match_id=<id>`  
   Optional: `&court_id=<id>`. One shareable link; no login.

8. **Upload to cloud (R2)** – after run-match, if R2 is configured:  
   `python3 -m src.app.cli upload-match --match_id <id>`

---

### Deploy (so anyone can open the user link)

**Detailed step-by-step:** see **[DEPLOY.md](DEPLOY.md)** (Render, Railway, scaling, renaming).

The API can run **without a local DB or disk**: if R2 is configured, it serves match data and report from R2. So you can deploy to a free tier and share `/view?match_id=xxx`.

**1. Upload at least one match to R2** (from your machine):

```bash
python3 -m src.app.cli upload-match --match_id match_2026_02_25_022906
```

**2. Deploy the API** with one of the options below. Set these **environment variables** in the host’s dashboard:

- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ACCOUNT_ID`

Optional: `COURTFLOW_DATA_DIR` (only if you run the pipeline on the server and need persistent data).

#### Option A – Render (free tier)

1. Go to [render.com](https://render.com), sign in, connect your GitHub repo.
2. **New → Web Service**. Select the repo and branch.
3. **Build**:  
   - Build command: `pip install -r requirements.txt`  
   - Start command: `uvicorn src.app.api:app --host 0.0.0.0 --port $PORT`
4. **Environment**: Add the four R2 variables above (and `PORT` is set by Render).
5. Deploy. Your URL will be like `https://courtflow-xxx.onrender.com`.
6. Share: `https://courtflow-xxx.onrender.com/view?match_id=match_2026_02_25_022906`

#### Option B – Railway

1. Go to [railway.app](https://railway.app), connect the repo and create a new project.
2. Add a **Web Service**; Railway will detect the repo. Use a **Dockerfile** (we provide one) or set:
   - Start: `uvicorn src.app.api:app --host 0.0.0.0 --port $PORT`
   - Build: `pip install -r requirements.txt`
3. In **Variables**, add the four R2 env vars. Set `PORT` only if Railway doesn’t set it.
4. Deploy and use the generated URL: `https://xxx.up.railway.app/view?match_id=...`

#### Option C – Docker (any host)

```bash
docker build -t courtflow-api .
docker run -p 8000:8000 \
  -e R2_ACCESS_KEY_ID=... \
  -e R2_SECRET_ACCESS_KEY=... \
  -e R2_BUCKET=courtflow \
  -e R2_ACCOUNT_ID=... \
  courtflow-api
```

Then open `http://localhost:8000/view?match_id=...` (or your server’s public URL).

---

## High-level architecture

- **Video processing (edge)**: Python + FFmpeg + OpenCV
- **Local DB**: SQLite (match registry, artifacts)
- **Cloud storage**: Cloudflare R2 (highlights + report; presigned URLs)
- **API**: FastAPI (matches, report, meta, artifacts, cloud upload, `/view` user UI)
- **Ops dashboard**: Streamlit (full internal view)
- **User UI**: Single-page dashboard at `/view` (Phase 1 report + highlights)

---

## Data contracts (source of truth)

All core contracts live in `src/domain/models.py` (Python dataclasses) and
`src/domain/report_contract.py` (empty_report, empty_tracks).

- **DB entities**
  - `Court`: `court_id`, `site_name`, timestamps.
  - `Match`: match id, `court_id`, `source_type` (`"FILE"`/`"RTSP"`), `source_uri`,
    `output_dir`, `state`, timestamps, `last_error`.
  - `Artifact`: id, `match_id`, `type` (e.g. `RAW_CHUNK`, `HIGHLIGHTS_MP4`),
    `path`, `status`, `size_bytes`, timestamps.

- **Tracking**
  - `TrackRecord`: one detection/track per frame with:
    - `frame`, `timestamp`, `player_id`
    - `bbox_xyxy` \[x1, y1, x2, y2] (optional)
    - `x_pixel`, `y_pixel` (image space)
    - `x_court`, `y_court` (court space, may be `None` before calibration)
  - `Tracks = list[TrackRecord]`
  - Helper: `empty_tracks()` in `src/domain/report_contract.py` returns an empty list.

- **Calibration**
  - `CalibrationHomography`:
    - `schema_version`
    - `homography`: 9 floats (3×3 row-major)
    - `image_width`, `image_height`
    - optional `court_width_m`, `court_height_m`
  - Stored as JSON at `data/courts/<court_id>/calibration/homography.json` (or match dir for legacy).

- **Highlights + report**
  - `HighlightSegment`: `start`, `end`, `reason`.
  - `Phase1Report`:
    - `schema_version` (`phase1_v1`)
    - `match_id`, `court_id`, `generated_at`
    - `video`: basic video metadata
    - `summary`: top-level summary (e.g. duration)
    - `players`: per-player metrics (keys like `"0"`, `"1"`)
    - `team`: team-level metrics
    - `renders`: named render files (e.g. `"heatmap_player_0": "renders/heatmap_p0.png"`)
    - `highlights`: list[`HighlightSegment`]
    - `status`: processing status for the report
  - Helpers:
    - `new_phase1_report(...)` in `domain/models.py` builds the dataclass.
    - `empty_report(...)` in `src/domain/report_contract.py` returns a plain `dict` for JSON.

These contracts should remain stable. Intelligence modules should **conform
to them**, not modify them.

---

## Pipeline overview

Entry point: `src/pipeline/match_runner.py` → `run_match(match_id)` (or via `src.app.cli run-match`).

Rough flow:

1. **Look up match** in SQLite via `src.storage.match_db.get_match`.
2. **Ensure output dirs** via `src.pipeline.paths.ensure_match_dirs`.
3. **Ensure `meta/` + `reports/` exist** via match_runner helpers.
4. **Run stages 01–06** (see `src/pipeline/stages.py`):

   - **Stage 01 – Court calibration**
     - `stage_01_load_calibration(out_dir, video_path)`
     - Uses `src.court.calibration` (homography load/save). Expects
       `calibration/homography.json`. Stub-safe.

   - **Stage 02 – Player detection + tracking**
     - `stage_02_player_detection_tracking(out_dir, video_path)`
     - Uses `src.vision` (detection, tracking). Writes `tracks/tracks.json`.
     - Stub-safe.

   - **Stage 03 – Coordinate mapping (pixel → court)**
     - `stage_03_coordinate_mapping(out_dir)`
     - Loads homography + tracks; uses `src.vision.mapping` to fill
       `x_court` / `y_court`. Stub-safe.

   - **Stage 04 – Analytics report**
     - `stage_04_analytics_report(out_dir, match)`
     - Uses `src.analytics.report.build_phase1_report`. Writes
       `reports/report.json` (placeholder until analytics filled).

   - **Stage 05 – Renders / overlays**
     - `stage_05_render_overlays(out_dir)` — stub; future: heatmaps etc. in `renders/`.

   - **Stage 06 – Highlight export**
     - `stage_06_export_highlights(out_dir, cfg)`
     - Reads report; selects highlights (or time-sampled); cuts clips via
       `src.video.clips`; concat to `highlights/highlights.mp4`; updates report.

5. **Artifact registration**
   - Registers `HIGHLIGHTS_MP4` in SQLite via `add_artifact(...)`.
   - Streamlit dashboard shows artifacts and outputs.

All intelligence stages are wired but safe: if a team has not implemented
their module yet and raises `NotImplementedError`, the pipeline logs a
stub message and continues where possible.

---

## Intelligence modules (where to plug in)

Skeletons live under `src/court`, `src/vision`, `src/analytics`. Implement here; pipeline stays unchanged.

- **Court calibration**
  - `src/court/calibration/` — homography load/save, ROI, quick_check, capture, distortion.
  - Produce/store `CalibrationHomography` at `data/courts/<court_id>/calibration/` or match dir.

- **Detection & tracking**
  - `src/vision/detection/` (e.g. YOLO), `src/vision/tracking/` (MOT, ground_point, canonical_ids).
  - Output: `TrackRecord` list → `tracks/tracks.json`.

- **Coordinate mapping**
  - `src/vision/mapping/img_to_court.py` — pixel → court using homography.
  - Fill `x_court` / `y_court` on tracks.

- **Analytics (Phase 1 report)**
  - `src/analytics/report.py` — `build_phase1_report(...)`.
  - Start from `empty_report()`; read tracks + calibration.
  - Fill `summary`, `players`, `team`: match duration, heatmaps, zone coverage, net vs baseline %, team spacing, distance, speed, sprints, intensity timeline, etc.
  - Fill `renders` (paths to heatmaps etc.) and `highlights` (movement-based `HighlightSegment`s for Stage 06).

---

## Cloud upload (R2)

Cloudflare R2 is wired for uploading match artifacts and serving presigned links from the API and dashboard.

### What you need from Cloudflare

1. **Create an R2 bucket**  
   Cloudflare Dashboard → **R2** → **Create bucket** → pick a name (e.g. `courtflow`). You’ll use this as `R2_BUCKET`.

2. **Create an API token**  
   R2 → **Manage R2 API Tokens** → **Create API token**  
   - Permissions: **Object Read & Write**  
   - Copy the **Access Key ID** and **Secret Access Key** (secret is shown once).

3. **Account ID**  
   In the Cloudflare dashboard, open any R2 page; the URL looks like  
   `https://dash.cloudflare.com/<ACCOUNT_ID>/r2/...`  
   Use that `<ACCOUNT_ID>` as `R2_ACCOUNT_ID`.

### .env setup

Copy the example and fill in the R2 values:

```bash
cp .env.example .env
```

Edit `.env` and set (no quotes needed):

```
R2_ACCESS_KEY_ID=your_access_key_from_step_2
R2_SECRET_ACCESS_KEY=your_secret_key_from_step_2
R2_BUCKET=courtflow
R2_ACCOUNT_ID=your_account_id_from_step_3
```

Save the file. The app loads `.env` automatically (no need to export in the shell).

### How to upload and get links

- **CLI**: After `run-match`, run  
  `python3 -m src.app.cli upload-match --match_id <id>`
- **API**: `POST /matches/{match_id}/cloud/upload` uploads and returns presigned URLs.  
  `GET /matches/{match_id}/cloud/urls` returns presigned URLs for highlights and report (1h default).
- **Dashboard**: Open the **Cloud (R2)** section → **Upload to R2**, then **Get cloud links** to watch highlights from R2. (API must be running: `python3 -m uvicorn src.app.api:app --reload`.)

Code: `src/cloud/storage_r2.py`, `src/cloud/upload.py`. Dependency: `boto3` (in requirements.txt).

---

## Dashboards and DB layer

- **SQLite DB + match store**
  - File: `src/storage/match_db.py`
    - Manages `courts`, `matches`, `artifacts` tables.
  - Data layout: `data/matches/<match_id>/` (see `src/pipeline/paths.py`).

- **Why Streamlit (and when to use something else)**
  - **Streamlit** is used for the ops dashboard because it’s Python-only and fast to build for internal/ops use. It’s less suited to polished public URLs and deep customization.
  - **Common for production user-facing dashboards**: a **React/Next.js** (or Vue) front end calling your API, with routes like `/court/:courtId/match/:matchId`. That gives full control over layout, SEO, and shareable links.
  - **User UI (Phase 1 only)**: the API serves a **single-page user dashboard** at **`/view?match_id=xxx`** (optional `&court_id=xxx`). It shows only what Phase 1 defines for users: **AI Movement Intelligence Report** (match structure, positional intelligence, physical load) and **Highlights** (reel + clips). No ops details, raw DB state, or internal fields. File: `dashboard/view.html`.

- **Ops dashboard (Streamlit)**
  - File: `dashboard/app.py`
  - User enters **Court ID** (optional) + **Match ID** and clicks **View dashboard**, or selects from the list. Lets ops view:
    - Matches and their states.
    - Source video.
    - `meta/meta.json`, `tracks/tracks.json`, `calibration/homography.json`,
      `reports/report.json`.
    - `highlights/highlights.mp4` + per-clip videos.
    - Files in `renders/`.

---

## Running locally

- **Environment**: Python 3.9+ (3.10+ recommended). FFmpeg + ffprobe on PATH.
- **Install**: `python3 -m pip install -r requirements.txt`
- **API**: `python3 -m uvicorn src.app.api:app --reload` → then open http://127.0.0.1:8000/docs or http://127.0.0.1:8000/view?match_id=xxx
- **Ops dashboard**: `python3 -m streamlit run dashboard/app.py`
- **Process all FINALIZED matches**: `python3 -m src.app.cli daily-check`

Intelligence stages (court, vision, analytics) are stubs; you still get matches, meta, placeholder report, and time-sampled highlights from the pipeline.

---

## How to contribute (per team)

- **Read the contracts first**
  - `src/domain/models.py`
  - `src/schemas.py`

- **Implement your module**
  - Fill in the TODOs in your team’s file(s) without changing the function
    signatures.
  - Use the existing helpers (`read_json`, `write_json_atomic`,
    `load_tracks_from_json`, `dump_tracks_to_json`, etc.) to keep I/O
    consistent.

- **Keep JSON shape stable**
  - You can add fields inside `players`, `team`, `summary`, and `renders`,
    but avoid removing existing top-level keys unless the contract is
    updated for everyone.

---

## Next steps

- Implement court calibration, detection/tracking, and analytics in
  `src/court`, `src/vision`, `src/analytics` (real homography, YOLO/MOT, movement metrics).
- Deploy API + `/view` so users can open the shareable link from anywhere.
- Optional: React/Next.js coach dashboard on top of the same API.

