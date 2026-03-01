# Contracts, data structures, and interfaces

Single reference for diagrams, interfaces, contracts, and data structures. The system is working end-to-end; this doc is for drawing and formalizing it.

---

## 1. Pipeline flow (for diagrams)

```
Ingest (CLI) → Match in DB + data/matches/<match_id>/raw/match.mp4
                    ↓
run-match: stage_01 load calibration → stage_02 track → stage_03 map → stage_04 report → stage_05 renders → stage_06 highlights
                    ↓
Outputs: tracks/tracks.json, reports/report.json, reports/heatmap.png, renders/*.png|*.mp4, highlights/highlights.mp4
```

Calibration is one-time per court (manual or identity); stage_01 copies homography into match dir when OK.

---

## 2. Data structures (canonical)

**Domain (src/domain/models.py)**  
- **Match**: match_id, court_id, source_type, source_uri, output_dir, state (MatchState), started_at, ended_at, last_error, created_at, updated_at  
- **TrackRecord**: frame, timestamp, player_id, bbox_xyxy (optional), x_pixel, y_pixel, x_court (optional), y_court (optional)  
- **Tracks**: List[TrackRecord]  
- **CalibrationHomography**: schema_version, homography (9 floats row-major), image_width, image_height, court_width_m (optional), court_height_m (optional)  
- **Phase1Report**: schema_version, match_id, court_id, generated_at, video (dict), summary (dict), players (dict), team (dict), renders (dict), highlights (list), status  

**Report JSON (on disk and API)**  
- Same as Phase1Report plus: analytics (e.g. heatmap_path), padel (rally_metrics, shot_speeds, wall_usage, player_stats_sample), exported_highlights, highlights_mp4 when filled by pipeline.  

**Calibration artifacts (court dir)**  
- homography.json: CalibrationHomography  
- roi_polygon.json: { schema_version, points_px: [[x,y], ...] }  
- calib_frame.jpg, roi_mask.png: optional  

---

## 3. File layout

- **data/matches/<match_id>/**  
  raw/match.mp4, meta/meta.json, calibration/homography.json (copy), tracks/tracks.json, reports/report.json, reports/heatmap.png, renders/*, highlights/highlights.mp4, highlights/clips/*.mp4  
- **data/courts/<court_id>/calibration/**  
  homography.json, roi_polygon.json, roi_mask.png, calib_frame.jpg (optional)  

---

## 4. Key interfaces (contracts)

**Intelligence (vision)**  
- **Entry**: `run_tracking(video_path, court_id, match_dir, sample_every_n_frames=5, conf=0.4, iou=0.5, tracker=None) -> List[dict]`  
- **Contract**: Each dict has frame, timestamp, player_id, x_pixel, y_pixel, bbox_xyxy (optional). Stage_03 adds x_court, y_court.  
- **Implemented in**: src/vision/pipeline.py (calls detection, ROI filter, ground point).  

**Report build**  
- **Entry**: `build_phase1_report(match, video_meta=, tracks_path=, calib_path=, out_dir=) -> Path`  
- **Contract**: Writes report.json with summary, players, analytics.heatmap_path, padel (rally_metrics, shot_speeds, wall_usage, player_stats_sample).  

**API (REST)**  
- GET /matches, GET /matches/{id}, GET /matches/{id}/report, GET /matches/{id}/report/heatmap, GET /matches/{id}/highlights/video, GET /matches/{id}/meta  
- GET /matches/{id}/cloud/urls, POST /matches/{id}/cloud/upload  
- Response shapes: MatchOut (match_id, court_id, source_type, source_uri, output_dir, state, ...), report = full report dict.  

**Calibration save/load**  
- `save_calibration_artifacts(calib_dir, calib, calib_frame=, roi_polygon_px=)`  
- `load_calibration_artifacts(calib_dir) -> CalibrationHomography | None`  

---

## 5. What you have vs what to do

**You have:**  
- Working pipeline and deployed site.  
- Domain models and report shape in code (models.py, report_contract.py).  
- Path layout in pipeline/paths.py and config/settings.py.  
- Vision contract in docs/INTELLIGENCE.md and vision/pipeline.py.  
- API routes and response types in src/app/api.py.  

**Enough to:**  
- Draw pipeline and data-flow diagrams (ingest → stages → outputs).  
- Draw file/dir layout and which stage reads/writes what.  
- Write an interface/contract doc (APIs, run_tracking, build_phase1_report, calibration).  
- Freeze data structures (TrackRecord, report JSON, homography, ROI) in a single “schema” doc or OpenAPI + a short “data structures” section.  

**Optional extras:**  
- OpenAPI/JSON Schema for the report and for API responses.  
- One diagram (e.g. Mermaid) in-repo for pipeline + one for “where data lives.”  
- Explicit “ball pipeline” placeholder (future ball_shot_frames, bounce_events) in the contract doc so padel analytics interfaces stay clear.  

So yes: you have a full system working and enough info to do diagrams, interfaces, contracts, and data structures; this doc plus the code and existing docs (INTELLIGENCE, COURT_CALIBRATION, TESTING) are the single reference.
