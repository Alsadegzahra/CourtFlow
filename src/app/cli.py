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


def _image_size(path: Path) -> tuple:
    """Return (width, height) from image or first frame of video."""
    import cv2
    path = Path(path)
    suf = path.suffix.lower()
    if suf in (".mp4", ".mov", ".avi", ".mkv"):
        cap = cv2.VideoCapture(str(path))
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError(f"Could not read first frame: {path}")
        h, w = frame.shape[:2]
        return (w, h)
    img = cv2.imread(str(path))
    if img is None:
        raise RuntimeError(f"Could not read image: {path}")
    h, w = img.shape[:2]
    return (w, h)


def cmd_calibrate_court(args: argparse.Namespace) -> None:
    """calibrate-court: manual calibration once per court. Use --identity from image/video or --homography_file to copy."""
    from src.config.settings import ensure_dirs
    from src.pipeline.paths import court_calibration_dir
    from src.court.calibration.artifacts import save_calibration_artifacts
    from src.court.calibration.homography import load_homography, identity_homography, save_homography

    ensure_dirs()
    court_id = getattr(args, "court_id", "court_001")
    calib_dir = court_calibration_dir(court_id)
    homography_file = getattr(args, "homography_file", None)
    image_path = getattr(args, "image", None)
    use_identity = getattr(args, "identity", False)

    if homography_file:
        path = Path(homography_file)
        if not path.exists():
            raise FileNotFoundError(f"Homography file not found: {path}")
        calib = load_homography(path)
        if not calib:
            raise ValueError(f"Invalid homography file: {path}")
        save_calibration_artifacts(calib_dir, calib)
        print(f"Saved calibration from {path} to court {court_id}.")
        return

    if use_identity and image_path:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image/video not found: {path}")
        w, h = _image_size(path)
        calib = identity_homography(w, h)
        save_calibration_artifacts(calib_dir, calib)
        print(f"Saved identity calibration (image {w}x{h}) for court {court_id}.")
        return

    if image_path and not use_identity:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image/video not found: {path}")
        from src.court.calibration.click_calibrate import calibrate_from_clicks
        court_w = getattr(args, "court_width_m", 1.0)
        court_h = getattr(args, "court_height_m", 1.0)
        calib, calib_frame, points_px = calibrate_from_clicks(path, court_width_m=court_w, court_height_m=court_h)
        save_calibration_artifacts(
            calib_dir, calib,
            calib_frame=calib_frame,
            roi_polygon_px=[(float(x), float(y)) for x, y in points_px],
        )
        print(f"Saved manual (click) calibration + calib_frame + ROI for court {court_id}.")
        return

    if use_identity:
        print("Use --image <path> with --identity to create calibration from image/video size.")
        return
    print("Use --image <path> to click 4 court corners, --identity --image <path> for identity, or --homography_file <path> to copy.")


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
    p_cal = sub.add_parser("calibrate-court", help="Manual calibration once per court")
    p_cal.add_argument("--court_id", default="court_001")
    p_cal.add_argument("--image", help="Image or video: with --identity use frame size; else open window to click 4 court corners")
    p_cal.add_argument("--identity", action="store_true", help="Write identity homography from --image dimensions (no clicks)")
    p_cal.add_argument("--homography_file", help="Path to existing homography.json to copy into court")
    p_cal.add_argument("--court_width_m", type=float, default=1.0, help="Court width in meters (for click calibration)")
    p_cal.add_argument("--court_height_m", type=float, default=1.0, help="Court height in meters (for click calibration)")
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
