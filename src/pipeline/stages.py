"""
Stage functions: calibration, track, map, report, renders, highlights.
Uses: court/calibration, vision (stubs), storage/tracks_db, analytics/report, highlights/export, video/clips, utils/io.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.utils.io import read_json, write_json
from src.utils.time import now_iso
from src.domain.models import CalibrationHomography
from src.court.calibration.artifacts import load_calibration_artifacts
from src.analytics.report import build_phase1_report
from src.highlights.export import export_highlights
from src.video.clips import probe_duration


def _meta_path(match_dir: Path) -> Path:
    return match_dir / "meta" / "meta.json"


def _report_path(match_dir: Path) -> Path:
    return match_dir / "reports" / "report.json"


def ensure_meta_and_report(match_dir: Path, video_path: Path) -> None:
    """Ensure meta/meta.json and reports/report.json exist."""
    meta_path = _meta_path(match_dir)
    report_path = _report_path(match_dir)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not meta_path.exists():
        duration = probe_duration(video_path) if video_path.exists() else 0.0
        write_json(meta_path, {
            "status": "created",
            "created_at": now_iso(),
            "last_updated_at": now_iso(),
            "video_path": str(video_path),
            "video": {"duration_seconds": duration, "fps": 30},
        })
    if not report_path.exists():
        write_json(report_path, {"created_at": now_iso(), "highlights": []})


def update_meta_status(match_dir: Path, status: str) -> None:
    meta = read_json(_meta_path(match_dir))
    meta["status"] = status
    meta["last_updated_at"] = now_iso()
    write_json(_meta_path(match_dir), meta)


def stage_01_load_calibration(match_dir: Path, court_id: str, video_path: Path) -> None:
    """
    Per-match calibration flow: manual once per court, then light auto-check per match.
    If check fails → try auto-fix; if that fails → proceed without court mapping (manual later).
    """
    from src.domain.enums import CalibrationStatus
    from src.court.calibration.quick_check import run_quick_check
    from src.court.calibration.artifacts import save_calibration_artifacts
    from src.court.calibration.auto_fix import try_auto_fix
    from src.pipeline.paths import court_calibration_dir

    calib_dir = court_calibration_dir(court_id)
    calib = load_calibration_artifacts(calib_dir)

    if not calib:
        print("   No calibration for this court; run manual calibration once per court.")
        return

    # Light per-match check
    status = run_quick_check(court_id, video_path=video_path)
    if status == CalibrationStatus.OK:
        print(f"   ✓ Calibration OK for court {court_id}")
    elif status == CalibrationStatus.WARN:
        print(f"   ⚠ Calibration warn (e.g. resolution mismatch) for court {court_id}; using anyway.")

    if status == CalibrationStatus.FAIL:
        print("   Calibration check failed; trying auto-fix...")
        new_calib = try_auto_fix(court_id, video_path)
        if new_calib:
            save_calibration_artifacts(calib_dir, new_calib)
            calib = new_calib
            print("   ✓ Auto-fix applied; calibration updated.")
        else:
            print("   Auto-fix did not recover calibration; run manual calibration. Proceeding without court mapping.")
            return

    # Copy to match dir so stage 03/04 find it
    match_calib_dir = match_dir / "calibration"
    match_calib_dir.mkdir(parents=True, exist_ok=True)
    from src.court.calibration.homography import save_homography
    save_homography(match_calib_dir / "homography.json", calib)


def stage_02_track(
    match_dir: Path,
    video_path: Path,
    court_id: str,
    *,
    sample_every_n_frames: int = 5,
    conf: float = 0.4,
) -> None:
    """Player detection + tracking -> tracks/tracks.json. Uses YOLO track + ROI filter + ground point."""
    import cv2
    from src.utils.io import write_json_atomic_any
    from src.pipeline.paths import court_calibration_dir

    tracks_dir = match_dir / "tracks"
    tracks_dir.mkdir(parents=True, exist_ok=True)
    tracks_file = tracks_dir / "tracks.json"

    if not video_path.exists():
        write_json(tracks_file, [])
        print("   (skip) Video not found; empty tracks.")
        return

    try:
        from src.vision.detection.yolo import _get_model, track_persons
        from src.vision.roi_filter.filter import load_roi_for_match, filter_detections_by_roi
        from src.vision.tracking.ground_point import bbox_to_ground_point
    except ImportError as e:
        write_json(tracks_file, [])
        print("   (skip) Vision deps missing (pip install ultralytics); empty tracks.")
        return

    # Load ROI if available (match calibration or court)
    match_calib_dir = match_dir / "calibration"
    court_calib_dir = court_calibration_dir(court_id)
    roi_polygon = load_roi_for_match(match_calib_dir, court_calib_dir)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    model = _get_model()
    tracks: List[dict] = []
    frame_idx = 0
    processed = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        if frame_idx % sample_every_n_frames != 0:
            frame_idx += 1
            continue
        dets = track_persons(frame, model=model, conf=conf)
        if roi_polygon:
            dets = filter_detections_by_roi(dets, roi_polygon)
        for d in dets:
            track_id = d.get("track_id", -1)
            if track_id < 0:
                continue
            x, y = bbox_to_ground_point(d["bbox_xyxy"])
            tracks.append({
                "frame": frame_idx,
                "timestamp": round(frame_idx / fps, 3),
                "player_id": track_id,
                "x_pixel": round(x, 2),
                "y_pixel": round(y, 2),
                "bbox_xyxy": d["bbox_xyxy"],
            })
        processed += 1
        frame_idx += 1
    cap.release()

    write_json_atomic_any(tracks_file, tracks)
    n_players = len(set(t["player_id"] for t in tracks))
    print(f"   ✓ Tracked {len(tracks)} points from {processed} frames ({n_players} players).")


def stage_03_map(match_dir: Path, court_id: str) -> None:
    """Pixel -> court mapping: load tracks + calibration, fill x_court/y_court, write back."""
    from src.utils.io import write_json_atomic_any
    tracks_path = match_dir / "tracks" / "tracks.json"
    calib_path = match_dir / "calibration" / "homography.json"
    if not calib_path.exists():
        from src.pipeline.paths import court_calibration_dir
        cal_dir = court_calibration_dir(court_id)
        calib_path = cal_dir / "homography.json"
    if not calib_path.exists() or not tracks_path.exists():
        print("   (skip) No calibration or tracks for coordinate mapping.")
        return
    calib = load_calibration_artifacts(calib_path.parent)
    if not calib:
        print("   (skip) Could not load calibration for mapping.")
        return
    tracks_data = read_json(tracks_path)
    if not isinstance(tracks_data, list) or not tracks_data:
        print("   (skip) No tracks to map.")
        return
    from src.vision.mapping.img_to_court import apply_calibration_to_tracks
    apply_calibration_to_tracks(tracks_data, calib)
    write_json_atomic_any(tracks_path, tracks_data)
    print(f"   ✓ Mapped {len(tracks_data)} track points to court coordinates.")


def stage_04_report(match_dir: Path, match: Dict[str, Any]) -> None:
    """Build Phase1Report -> reports/report.json."""
    meta = read_json(_meta_path(match_dir))
    video_meta = meta.get("video", {})
    tracks_path = match_dir / "tracks" / "tracks.json"
    calib_path = match_dir / "calibration" / "homography.json"
    if not calib_path.exists():
        from src.pipeline.paths import court_calibration_dir
        cal_dir = court_calibration_dir(match["court_id"])
        homography_file = cal_dir / "homography.json"
        calib_path = homography_file if homography_file.exists() else None
    report_path = build_phase1_report(
        match,
        video_meta=video_meta,
        tracks_path=tracks_path if tracks_path.exists() else None,
        calib_path=calib_path,
        out_dir=match_dir,
    )
    print(f"   ✓ Report written: {report_path}")


def stage_05_renders(match_dir: Path, video_path: Path) -> None:
    """Render detection/tracking overlays: sample PNGs + short overlay video."""
    import cv2
    from src.utils.io import read_json
    from src.video.overlay import draw_tracks_on_frame, group_tracks_by_frame

    renders_dir = match_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    tracks_path = match_dir / "tracks" / "tracks.json"
    if not tracks_path.exists() or not video_path.exists():
        print("   (skip) No tracks or video for renders.")
        return

    tracks = read_json(tracks_path)
    if not isinstance(tracks, list) or not tracks:
        print("   (skip) Empty tracks; no overlays.")
        return
    by_frame = group_tracks_by_frame(tracks)
    frame_indices = sorted(by_frame.keys())
    if not frame_indices:
        print("   (skip) No track frames.")
        return

    cap = cv2.VideoCapture(str(video_path))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    # Sample images: up to 5 frames spread across the video
    samples = []
    for i in [0, 0.25, 0.5, 0.75, 1.0]:
        idx = frame_indices[min(int(len(frame_indices) * i), len(frame_indices) - 1)]
        samples.append(idx)
    samples = sorted(set(samples))
    for fi in samples:
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        tr = by_frame.get(fi, [])
        out = draw_tracks_on_frame(frame, tr)
        png_path = renders_dir / f"track_overlay_frame_{fi:05d}.png"
        cv2.imwrite(str(png_path), out)
    print(f"   ✓ Wrote {len(samples)} sample images to renders/")

    # Short overlay video (first 10 sec or 300 frames)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    max_overlay_frames = min(300, n_frames)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_video = renders_dir / "track_overlay_preview.mp4"
    writer = cv2.VideoWriter(
        str(out_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )
    for frame_idx in range(max_overlay_frames):
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        tr = by_frame.get(frame_idx, [])
        out = draw_tracks_on_frame(frame, tr)
        writer.write(out)
    writer.release()
    cap.release()
    print(f"   ✓ Wrote overlay video: renders/track_overlay_preview.mp4 ({max_overlay_frames} frames)")


def stage_06_highlights(
    match_dir: Path,
    video_path: Path,
    *,
    clip_len_s: float = 12.0,
    every_s: float = 60.0,
    max_clips: int = 10,
) -> Path:
    """Export highlight clips and concat to highlights/highlights.mp4."""
    report_path = _report_path(match_dir)
    return export_highlights(
        match_dir,
        video_path,
        report_path,
        clip_len_s=clip_len_s,
        every_s=every_s,
        max_clips=max_clips,
    )
