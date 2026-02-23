## B5 – Player Tracking

- **Responsibility**: Detect and track players over time in the match video, producing `TrackRecord` entries and writing `tracks/tracks.json`.
- **Main code**: `tracking.py`

### Tools / Libraries

- _(To be decided by the B5 team — e.g., YOLO/Detectron/etc. for detection, Deep SORT/ByteTrack/etc. for tracking.)_

### Models / Intelligence

- Player detector (people / players from overhead view)
- Multi-object tracker to maintain `player_id` over time
- Any smoothing / interpolation logic for stable tracks

