## CourtFlow – Phase 1 Skeleton

CourtFlow is an MVP system for turning raw match video into structured
analytics and highlight videos. This repo now contains a **full skeleton +
contracts** for the entire pipeline and cloud stack so that model/infra
teams can plug in their logic without rewriting glue code.

This README is written for teammates who will implement the actual
intelligence (vision models, analytics, cloud upload, dashboards).

---

## High-level architecture

- **Video processing (edge)**: Python + FFmpeg + OpenCV
- **Local DB**: SQLite (for ops / local runs)
- **Cloud storage (planned)**: Cloudflare R2
- **Cloud DB (planned)**: Supabase
- **API backend (planned)**: FastAPI
- **Ops dashboard**: Streamlit
- **Coach dashboard (planned)**: Next.js

For now, everything runs locally with SQLite + filesystem storage. Cloud
pieces are defined as interfaces and stubs.

---

## Data contracts (source of truth)

All core contracts live in `src/domain/models.py` (Python dataclasses) and
are surfaced as simple helpers in `src/schemas.py`.

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
  - Helper: `empty_tracks()` in `src/schemas.py` returns an empty, contract-shaped list.

- **Calibration**
  - `CalibrationHomography`:
    - `schema_version`
    - `homography`: 9 floats (3×3 row-major)
    - `image_width`, `image_height`
    - optional `court_width_m`, `court_height_m`
  - Stored as JSON at `output_dir/calibration/homography.json`.

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
    - `empty_report(...)` in `src/schemas.py` returns a plain `dict` for JSON.

These contracts should remain stable. Intelligence modules should **conform
to them**, not modify them.

---

## Pipeline overview

Entry point: `src/pipeline/pipeline.py` → `run_pipeline_for_match(match_id)`.

Rough flow:

1. **Look up match** in SQLite via `b2_storage.db.get_match`.
2. **Ensure output dirs** via `b2_storage.match_store.ensure_match_dirs`.
3. **Ensure `meta/` + `reports/` exist** via `_ensure_meta_and_report`.
4. **Run stages 01–06**:

   - **Stage 01 – Court calibration**
     - Function: `stage_01_load_calibration(out_dir, video_path)`
     - Calls `b4_court_model.calibration.load_or_estimate_calibration(...)`.
     - Expects a `CalibrationHomography`, saved to
       `calibration/homography.json`.
     - If B4 is not implemented yet (raises `NotImplementedError`), the
       stage logs a stub message and continues.

   - **Stage 02 – Player detection + tracking**
     - Function: `stage_02_player_detection_tracking(out_dir, video_path)`
     - Calls `b5_player_tracking.tracking.run_player_tracking(...)`.
     - Expects a `Tracks` list serialized as JSON at
       `tracks/tracks.json` (list of `TrackRecord`-shaped dicts).
     - On `NotImplementedError`, logs a stub message.

   - **Stage 03 – Coordinate mapping (pixel → court)**
     - Function: `stage_03_coordinate_mapping(out_dir)`
     - If `tracks/tracks.json` and `calibration/homography.json` are both
       present:
       - Loads `CalibrationHomography` from JSON.
       - Calls `b5b_coord_conversion.coords.apply_calibration_to_tracks(...)`
         to fill `x_court` / `y_court` on each `TrackRecord`.
     - On `NotImplementedError` or missing files, logs and skips.

   - **Stage 04 – Analytics report**
     - Function: `stage_04_analytics_report(out_dir, match)`
     - Calls `b6_movement_metrics.analytics.build_phase1_report(...)`.
     - Currently writes a **placeholder** `reports/report.json` using
       `empty_report(...)`, but is the place where real analytics will live.

   - **Stage 05 – Renders / overlays**
     - Function: `stage_05_render_overlays(out_dir)`
     - Currently a stub that only logs. Future Z-team code will generate
       images/videos in `renders/` and update the report’s `renders` field.

   - **Stage 06 – Highlight export**
     - Function: `stage_06_export_highlights(out_dir, cfg)`
     - Logic:
       - Reads `meta/meta.json` and `reports/report.json`.
       - Uses `report["highlights"]` if present; otherwise, generates
         time-sampled dummy clips.
       - Cuts individual clips with FFmpeg into `highlights/clips/`.
       - Concatenates them into `highlights/highlights.mp4`.
       - Writes `exported_highlights` and `highlights_mp4` back into
         `report.json`.

5. **Artifact registration**
   - When the pipeline finishes, it registers a `HIGHLIGHTS_MP4` artifact
     in SQLite via `add_artifact(...)`.
   - The Streamlit dashboard reads this to show what was produced.

All intelligence stages are wired but safe: if a team has not implemented
their module yet and raises `NotImplementedError`, the pipeline logs a
stub message and continues where possible.

---

## Intelligence modules (what each team owns)

All of these modules are **pure skeletons** with clear TODOs and
docstrings. Teams plug in their logic here.

- **B4 – Court model**
  - File: `src/b4_court_model/calibration.py`
  - Responsibilities:
    - Run a court detection / calibration model on the input video.
    - Produce a `CalibrationHomography`.
    - Load or reuse existing calibration if appropriate.

- **B5 – Player tracking**
  - File: `src/b5_player_tracking/tracking.py`
  - Responsibilities:
    - Run player detector + tracker on the video.
    - Produce a list of `TrackRecord` entries (conforming to the contract).
    - Serialize to `tracks/tracks.json`.
    - Optionally, enrich `validate_tracks_contract(...)` with stricter checks.

- **B5b – Coordinate conversion**
  - File: `src/b5b_coord_conversion/coords.py`
  - Responsibilities:
    - Load tracks from JSON.
    - Use `CalibrationHomography` to compute `x_court` / `y_court` for each
      track.
    - Write updated tracks back with an atomic JSON write.
  - Helpers:
    - `load_tracks_from_json(...)` and `dump_tracks_to_json(...)` centralize
      JSON ↔ dataclass conversions.

- **B6 – Movement metrics & analytics**
  - File: `src/b6_movement_metrics/analytics.py`
  - Responsibilities:
    - Start from `empty_report(...)` / `Phase1Report`.
    - Read tracks + calibration.
    - Fill:
      - `summary` / `players` / `team` with Phase 1 movement + spatial metrics:
        - Match duration (time model)
        - Heatmaps per player
        - Zone coverage distribution (court zones)
        - Net vs baseline percentage
        - Team spacing visualization
        - Coverage gap detection
        - Positional drift over match
        - Transition frequency (baseline → net)
        - Positional efficiency score (composite index)
        - Distance covered
        - Average and maximum speed
        - Sprint count
        - Acceleration / deceleration indicators
        - Lateral movement percentage
        - Movement intensity timeline
        - Load distribution across the match (early / mid / late)
        - Motion-based fatigue / intensity drop-off trends
      - `renders` (filenames under `renders/`, e.g. heatmaps, spacing visuals)
      - `highlights` (movement-intensity-based `HighlightSegment`s that drive Stage 06)

---

## Cloud upload & storage (planned)

The cloud layer is defined but mostly stubbed, so infra can plug in real
Cloudflare R2 / Supabase without changing the pipeline.

- **Upload helper**
  - File: `src/b8_cloud_upload/uploader.py`
  - `BlobStorage` protocol:
    - `put_object(key: str, file_path: Path) -> str`  
      Uploads a local file under `key`, returns a URL or path string.
  - `upload_artifact_via_storage(artifact, storage)`:
    - Builds a storage key from `match_id`, artifact `type`, and filename.
    - Calls `storage.put_object(...)`.
    - Returns the resulting URL (and later can update the DB).

- **Storage backends**
  - File: `src/b9_cloud_storage/storage.py`
  - `LocalBlobStorage`:
    - Copies files to a local base directory; good for dev/testing.
  - `R2BlobStorage`:
    - Stub to be implemented with Cloudflare R2 SDK/API.

---

## Dashboards and DB layer

These components already work and are left mostly unchanged; they now sit
on top of the clearer contracts.

- **SQLite DB + match store**
  - File: `src/b2_storage/db.py`
    - Manages `courts`, `matches`, `artifacts` tables.
  - File: `src/b2_storage/match_store.py`
    - Defines the standard `data/outputs/<match_id>/` layout.

- **Ops dashboard (Streamlit)**
  - File: `dashboard/app.py`
  - Lets ops view:
    - Matches and their states.
    - Source video.
    - `meta/meta.json`, `tracks/tracks.json`, `calibration/homography.json`,
      `reports/report.json`.
    - `highlights/highlights.mp4` + per-clip videos.
    - Files in `renders/`.

Future work will introduce a FastAPI backend and a separate Next.js coach
dashboard that consume these same contracts.

---

## Running locally (current state)

> Note: exact commands may evolve; this reflects the current intent.

- **Environment**
  - Python 3.10+ recommended.
  - FFmpeg + ffprobe installed and on PATH.

- **Install dependencies**

```bash
pip install -r requirements.txt  # if present
```

- **Run the controller loop (process FINALIZED matches)**

```bash
python -m src.b3_controller.controller
```

- **Run the Streamlit dashboard**

```bash
streamlit run dashboard/app.py
```

At this stage, most intelligence stages are placeholders; you should still
see matches, meta, and dummy highlights once the pipeline runs.

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

- Implement the B4/B5/B5b/B6 intelligence modules against real or pretrained
  models.
- Add a FastAPI backend that exposes matches, artifacts, and reports via a
  stable API.
- Add Cloudflare R2 + Supabase integrations using the BlobStorage and
  repository interfaces.
- Build a Next.js coach dashboard on top of the API.

