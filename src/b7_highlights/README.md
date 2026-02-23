## B7 – Highlights (Video Export)

- **Responsibility**: Turn highlight time windows (from the report or dummy logic) into per-clip MP4s and a concatenated `highlights.mp4` file.
- **Main code**: `highlights.py` (plus highlight export stage in `pipeline.py`)

### Tools / Libraries

- FFmpeg / ffprobe (via CLI)
- Python standard library (`subprocess`, `pathlib`)

### Models / Intelligence

- _(Phase 1 highlight selection is driven by movement intensity from B6; this block focuses on video cutting/concat, not ML.)_

