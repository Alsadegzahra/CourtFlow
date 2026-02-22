# src/pipeline/run_match.py
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from src.common.config import OUTPUTS_DIR, ensure_dirs
from src.b2_storage.db import init_db, upsert_court, create_match, update_match, add_artifact
from src.b2_storage.match_store import ensure_match_dirs, raw_chunks_dir
from src.b1_capture.recorder_ffmpeg import record_file_to_chunks
from src.pipeline.pipeline import run_pipeline_for_match, HighlightConfig


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_match_id(prefix: str = "match") -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--court_id", default="COURT_001")
    p.add_argument("--site_name", default="CourtFlow MVP")
    p.add_argument("--input", required=True, help="Path to input video (FILE mode)")
    p.add_argument("--chunk_sec", type=int, default=300)

    # highlight config (dummy logic)
    p.add_argument("--clip_len", type=float, default=12.0)
    p.add_argument("--every", type=float, default=60.0)
    p.add_argument("--max_clips", type=int, default=10)

    args = p.parse_args()

    ensure_dirs()
    init_db()
    upsert_court(args.court_id, args.site_name)

    match_id = make_match_id("sample")
    output_dir = str(OUTPUTS_DIR / match_id)
    ensure_match_dirs(output_dir)

    create_match(
        match_id=match_id,
        court_id=args.court_id,
        source_type="FILE",
        source_uri=args.input,
        output_dir=output_dir,
    )

    update_match(match_id, state="RECORDING", started_at=utcnow_iso())

    chunks_dir = raw_chunks_dir(output_dir)  # data/outputs/<match_id>/raw/chunks
    try:
        update_match(match_id, state="FINALIZING")
        record_file_to_chunks(args.input, str(chunks_dir), chunk_sec=args.chunk_sec)

        # Register RAW_CHUNK artifacts
        for chunk in sorted(Path(chunks_dir).glob("chunk_*.mp4")):
            add_artifact(
                match_id,
                "RAW_CHUNK",
                str(chunk),
                status="READY",
                size_bytes=chunk.stat().st_size,
            )

        update_match(match_id, state="FINALIZED", ended_at=utcnow_iso())
        print(f"[B2] FINALIZED {match_id} -> {output_dir}")

        # Now run pipeline (stubs + highlights mp4)
        cfg = HighlightConfig(
            clip_len_s=args.clip_len,
            every_s=args.every,
            max_clips=args.max_clips,
        )
        highlights = run_pipeline_for_match(match_id, cfg)
        print(f"[PIPELINE] DONE {match_id} -> highlights: {highlights}")

    except Exception as e:
        update_match(match_id, state="FAILED", last_error=str(e))
        raise


if __name__ == "__main__":
    main()