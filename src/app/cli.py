"""
CLI entry: calibrate-court, ingest-match, run-match, daily-check.
Uses: pipeline/match_runner, court/registry, video/ingest.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.config.settings import ensure_dirs, MATCHES_DIR
from src.storage.match_db import init_db, create_match, update_match, add_artifact, upsert_court
from src.pipeline.paths import ensure_match_dirs, match_dir, match_raw_dir
from src.pipeline.match_runner import run_match, HighlightConfig
from src.utils.time import utcnow_iso
from src.video.ingest import ingest_file_to_mp4


def _make_match_id(prefix: str = "match") -> str:
    from datetime import datetime
    return f"{prefix}_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}"


def cmd_calibrate_court(args: argparse.Namespace) -> None:
    """calibrate-court: capture and/or compute calibration for a court (stub)."""
    print("(stub) calibrate-court not implemented. Use court/calibration modules when ready.")


def cmd_ingest_match(args: argparse.Namespace) -> None:
    """ingest-match: create match, ingest video to raw/match.mp4, set FINALIZED."""
    ensure_dirs()
    init_db()
    upsert_court(args.court_id, getattr(args, "site_name", None))

    match_id = _make_match_id("match")
    out_dir = match_dir(match_id)
    ensure_match_dirs(match_id)
    output_dir_str = str(out_dir)

    create_match(
        match_id=match_id,
        court_id=args.court_id,
        source_type="FILE",
        source_uri=args.input,
        output_dir=output_dir_str,
    )
    update_match(match_id, state="RECORDING", started_at=utcnow_iso())

    raw_dir = match_raw_dir(match_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    match_mp4 = raw_dir / "match.mp4"
    ingest_file_to_mp4(Path(args.input), match_mp4)
    # Optionally register raw artifact
    add_artifact(match_id, "RAW_MERGED", str(match_mp4), status="READY", size_bytes=match_mp4.stat().st_size)
    update_match(match_id, state="FINALIZED", ended_at=utcnow_iso())
    print(f"FINALIZED {match_id} -> {output_dir_str}")


def cmd_run_match(args: argparse.Namespace) -> None:
    """run-match: run pipeline for a match (by id or latest FINALIZED)."""
    ensure_dirs()
    init_db()

    match_id = getattr(args, "match_id", None)
    if not match_id:
        from src.storage.match_db import list_matches_by_state
        finalized = list_matches_by_state("FINALIZED")
        if not finalized:
            print("No FINALIZED match found. Run ingest-match first.")
            return
        match_id = finalized[0]["match_id"]
        print(f"Using match_id: {match_id}")

    cfg = HighlightConfig(
        clip_len_s=getattr(args, "clip_len", 12.0),
        every_s=getattr(args, "every", 60.0),
        max_clips=getattr(args, "max_clips", 10),
    )
    path = run_match(match_id, cfg)
    print(f"Highlights: {path}")


def cmd_daily_check(args: argparse.Namespace) -> None:
    """daily-check: process all FINALIZED matches (controller loop one-shot)."""
    from src.storage.match_db import list_matches_by_state
    ensure_dirs()
    init_db()
    for m in list_matches_by_state("FINALIZED"):
        try:
            run_match(m["match_id"])
        except Exception as e:
            print(f"FAILED {m['match_id']}: {e}")


def cmd_upload_match(args: argparse.Namespace) -> None:
    """upload-match: upload highlights and report for a match to Cloudflare R2."""
    from src.cloud.upload import upload_match_artifacts
    match_id = getattr(args, "match_id", None)
    if not match_id:
        from src.storage.match_db import list_matches
        matches = list_matches(limit=1)
        if not matches:
            print("No matches found. Run ingest-match and run-match first.")
            return
        match_id = matches[0]["match_id"]
        print(f"Using match_id: {match_id}")
    result = upload_match_artifacts(match_id)
    print(f"Uploaded keys: {result['keys']}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="courtflow")
    sub = ap.add_subparsers(dest="command", required=True)

    # calibrate-court
    p_cal = sub.add_parser("calibrate-court", help="Calibrate a court (stub)")
    p_cal.add_argument("--court_id", default="court_001")
    p_cal.set_defaults(func=cmd_calibrate_court)

    # ingest-match
    p_ing = sub.add_parser("ingest-match", help="Ingest video and create FINALIZED match")
    p_ing.add_argument("--court_id", default="court_001")
    p_ing.add_argument("--input", required=True, help="Path to input video")
    p_ing.set_defaults(func=cmd_ingest_match)

    # run-match
    p_run = sub.add_parser("run-match", help="Run pipeline for a match")
    p_run.add_argument("--match_id", default=None, help="Match ID (default: latest FINALIZED)")
    p_run.add_argument("--clip_len", type=float, default=12.0)
    p_run.add_argument("--every", type=float, default=60.0)
    p_run.add_argument("--max_clips", type=int, default=10)
    p_run.set_defaults(func=cmd_run_match)

    # daily-check
    p_daily = sub.add_parser("daily-check", help="Process all FINALIZED matches")
    p_daily.set_defaults(func=cmd_daily_check)

    # upload-match (cloud R2)
    p_up = sub.add_parser("upload-match", help="Upload match highlights + report to R2")
    p_up.add_argument("--match_id", default=None, help="Match ID (default: latest)")
    p_up.set_defaults(func=cmd_upload_match)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
