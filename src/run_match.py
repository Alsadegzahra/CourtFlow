import argparse
from datetime import datetime
from pathlib import Path

from src.config import MATCH_SUBFOLDERS, match_output_dir
from src.io_utils import ensure_dir, write_json
from src.video_utils import get_video_metadata
from src.schemas import empty_tracks, empty_report
from src.pipeline import run_pipeline


def make_match_id(video_path: Path) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = video_path.stem.replace(" ", "_")
    return f"{stem}_{ts}"


def create_match_structure(match_id: str) -> Path:
    out_dir = match_output_dir(match_id)
    ensure_dir(out_dir)
    for folder in MATCH_SUBFOLDERS:
        ensure_dir(out_dir / folder)
    return out_dir


def create_meta(match_id: str, video_path: Path, court_id: str, video_meta: dict) -> dict:
    return {
        "match_id": match_id,
        "video_path": str(video_path),
        "court_id": court_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "initialized",
        "pipeline_stages": [
            "00_ingest_video",
            "01_load_calibration",
            "02_player_detection_tracking",
            "03_coordinate_mapping",
            "04_analytics_report",
            "05_render_overlays",
            "06_export_highlights",
            "07_dashboard_ready",
        ],
        "video": video_meta,
    }


def initialize_placeholders(out_dir: Path, match_id: str, court_id: str, video_meta: dict) -> None:
    write_json(out_dir / "tracks" / "tracks.json", empty_tracks())
    report = empty_report(match_id=match_id, court_id=court_id, video_meta=video_meta)
    write_json(out_dir / "reports" / "report.json", report)


def run_match(video_path: Path, court_id: str = "court_001", run_after_init: bool = False) -> Path:
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    match_id = make_match_id(video_path)
    out_dir = create_match_structure(match_id)

    video_meta = get_video_metadata(video_path)

    meta = create_meta(match_id, video_path, court_id, video_meta)
    write_json(out_dir / "meta" / "meta.json", meta)

    initialize_placeholders(out_dir, match_id, court_id, video_meta)

    print("\n✅ Match initialized successfully")
    print(f"Match ID: {match_id}")
    print(f"Output directory: {out_dir}")
    print(f"Meta: {out_dir / 'meta' / 'meta.json'}")
    print(f"Tracks placeholder: {out_dir / 'tracks' / 'tracks.json'}")
    print(f"Report placeholder: {out_dir / 'reports' / 'report.json'}")

    if run_after_init:
        run_pipeline(out_dir)

    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True, help="Path to input match video")
    parser.add_argument("--court_id", type=str, default="court_001", help="Court ID (Phase 1 placeholder ok)")
    parser.add_argument("--run_pipeline", action="store_true", help="Run pipeline after initialization (stubs for now)")
    args = parser.parse_args()

    video_path = Path(args.video).expanduser().resolve()
    run_match(video_path, court_id=args.court_id, run_after_init=args.run_pipeline)


if __name__ == "__main__":
    main()
