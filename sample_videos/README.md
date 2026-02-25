# Sample videos

Drop match videos here (`.mp4`, `.mov`). From the project root:

```bash
# Ingest (creates a match and copies video to data/matches/<match_id>/raw/match.mp4)
python3 -m src.app.cli ingest-match --court_id court_001 --input sample_videos/your_video.mp4

# Run pipeline (report + highlights)
python3 -m src.app.cli run-match
```

Video files in this folder are gitignored. See main [README](../README.md) for full pipeline and tools.
