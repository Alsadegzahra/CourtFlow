# src/pipeline/pipeline.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.b2_storage.db import get_match, update_match, add_artifact
from src.b2_storage.match_store import ensure_match_dirs, highlights_dir, highlights_mp4_path
from src.common.io_utils import read_json, write_json
from src.common.video_utils import get_video_metadata
from src.common.ffmpeg_utils import cut_clip_ffmpeg, concat_clips_ffmpeg


@dataclass(frozen=True)
class HighlightConfig:
    clip_len_s: float = 12.0
    every_s: float = 60.0
    max_clips: int = 10


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _meta_path(out_dir: Path) -> Path:
    return out_dir / "meta" / "meta.json"


def _report_path(out_dir: Path) -> Path:
    return out_dir / "reports" / "report.json"


def _ensure_meta_and_report(out_dir: Path, video_path: Path) -> None:
    """
    Ensure meta/meta.json and reports/report.json exist so pipeline can run from scratch.
    """
    meta_path = _meta_path(out_dir)
    report_path = _report_path(out_dir)

    if not meta_path.exists():
        video_meta = get_video_metadata(video_path)
        meta: Dict[str, Any] = {
            "status": "created",
            "created_at": _now_iso(),
            "last_updated_at": _now_iso(),
            "video_path": str(video_path),
            "video": video_meta,
        }
        write_json(meta_path, meta)

    if not report_path.exists():
        report: Dict[str, Any] = {
            "created_at": _now_iso(),
            "highlights": [],  # later R will populate real highlights
        }
        write_json(report_path, report)


def _update_meta_status(out_dir: Path, status: str) -> None:
    meta_path = _meta_path(out_dir)
    meta = read_json(meta_path)
    meta["status"] = status
    meta["last_updated_at"] = _now_iso()
    write_json(meta_path, meta)


def stage_01_load_calibration(out_dir: Path) -> None:
    calib_path = out_dir / "calibration" / "homography.json"
    if calib_path.exists():
        print(f"   ✓ Found calibration: {calib_path.name}")
    else:
        print("   (stub) No calibration found yet. Proceeding without x_court/y_court mapping.")


def stage_02_player_detection_tracking(out_dir: Path) -> None:
    tracks_path = out_dir / "tracks" / "tracks.json"
    print(f"   (stub) Expected output: {tracks_path}")
    print("   (stub) S will populate tracks.json with per-frame player tracks.")


def stage_03_coordinate_mapping(out_dir: Path) -> None:
    print("   (stub) Will map x_pixel/y_pixel -> x_court/y_court when calibration exists.")


def stage_04_analytics_report(out_dir: Path) -> None:
    report_path = _report_path(out_dir)
    print(f"   (stub) Expected output: {report_path}")
    print("   (stub) R will compute Phase 1 metrics and write them into report.json.")


def stage_05_render_overlays(out_dir: Path) -> None:
    renders_dir = out_dir / "renders"
    print(f"   (stub) Will write render outputs to: {renders_dir}")


def _make_time_sampled_clips(duration_s: float, cfg: HighlightConfig) -> List[Dict[str, Any]]:
    """
    Dummy highlight logic: time-based sampling.
    """
    clips: List[Dict[str, Any]] = []
    for i in range(cfg.max_clips):
        start = i * cfg.every_s
        if start >= duration_s:
            break
        end = min(start + cfg.clip_len_s, duration_s)
        if end > start:
            clips.append({"start": float(start), "end": float(end), "reason": "time_sample"})
    return clips


def stage_06_export_highlights(out_dir: Path, cfg: HighlightConfig) -> Path:
    """
    Current MVP:
    - If report.json already has highlights, use them
    - Else generate time-sampled dummy clips
    - Export per-clip mp4s
    - Concatenate them into highlights/highlights.mp4
    - Save exported metadata back to report.json

    Returns: Path to highlights.mp4
    """
    meta_path = _meta_path(out_dir)
    report_path = _report_path(out_dir)

    meta = read_json(meta_path)
    report = read_json(report_path)

    video_path = Path(meta["video_path"])
    duration = float(meta.get("video", {}).get("duration_seconds") or 0.0)
    if duration <= 0:
        # fallback to avoid crashing; better than nothing
        duration = 60.0

    highlights = report.get("highlights", [])
    if not highlights:
        print("   No highlights found -> generating time-sampled dummy clips for testing.")
        highlights = _make_time_sampled_clips(duration, cfg)
        report["highlights"] = highlights
        write_json(report_path, report)

    hdir = highlights_dir(out_dir)
    hdir.mkdir(parents=True, exist_ok=True)
    clips_dir = hdir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    exported = []
    clip_paths: List[Path] = []

    for i, h in enumerate(highlights, start=1):
        out_file = clips_dir / f"clip_{i:03d}.mp4"
        cut_clip_ffmpeg(video_path, out_file, float(h["start"]), float(h["end"]))
        clip_paths.append(out_file)
        exported.append({"file": out_file.name, **h})

    # Build single highlights.mp4
    highlights_mp4 = highlights_mp4_path(out_dir)
    concat_clips_ffmpeg(clip_paths, highlights_mp4)

    report["exported_highlights"] = exported
    report["highlights_mp4"] = str(highlights_mp4)
    report["last_updated_at"] = _now_iso()
    write_json(report_path, report)

    print(f"   Exported {len(exported)} clips to: {clips_dir}")
    print(f"   Built highlights mp4: {highlights_mp4}")

    return highlights_mp4


def run_pipeline_for_match(match_id: str, cfg: HighlightConfig | None = None) -> Path:
    """
    DB-driven pipeline entrypoint (this is what B3 should call).
    - Reads match from DB
    - Ensures output dirs
    - Ensures meta/report exist
    - Runs stage pipeline (stubs + highlight export)
    - Writes artifact record HIGHLIGHTS_MP4
    - Updates match state DONE/FAILED

    Returns: Path to highlights mp4
    """
    cfg = cfg or HighlightConfig()

    match = get_match(match_id)
    if not match:
        raise ValueError(f"Match not found: {match_id}")

    source_type = match["source_type"]
    source_uri = match["source_uri"]
    out_dir = Path(match["output_dir"])

    if source_type != "FILE":
        raise RuntimeError(f"MVP pipeline only supports source_type=FILE (got {source_type})")

    video_path = Path(source_uri)
    if not video_path.exists():
        raise FileNotFoundError(f"Match source file not found: {video_path}")

    update_match(match_id, state="PROCESSING")

    try:
        ensure_match_dirs(out_dir)
        _ensure_meta_and_report(out_dir, video_path)

        print("\n🚀 Running Phase 1 pipeline...")

        _update_meta_status(out_dir, "running")

        print("\n[01] Load calibration")
        stage_01_load_calibration(out_dir)

        print("\n[02] Player detection + tracking")
        stage_02_player_detection_tracking(out_dir)

        print("\n[03] Coordinate mapping")
        stage_03_coordinate_mapping(out_dir)

        print("\n[04] Analytics report")
        stage_04_analytics_report(out_dir)

        print("\n[05] Render overlays / artifacts")
        stage_05_render_overlays(out_dir)

        print("\n[06] Export highlights")
        highlights_mp4 = stage_06_export_highlights(out_dir, cfg)

        _update_meta_status(out_dir, "pipeline_complete")

        # Register artifact in DB
        add_artifact(
            match_id=match_id,
            type_="HIGHLIGHTS_MP4",
            path=str(highlights_mp4),
            status="READY",
            size_bytes=highlights_mp4.stat().st_size if highlights_mp4.exists() else None,
        )

        update_match(match_id, state="DONE")
        print("\n✅ Pipeline finished (stubs). Next: plug in S/R/N implementations.")
        return highlights_mp4

    except Exception as e:
        update_match(match_id, state="FAILED", last_error=str(e))
        raise