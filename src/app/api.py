"""
FastAPI entry: matches, artifacts, reports.
Uses: storage/match_db, pipeline/paths, utils/io.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config.settings import PROJECT_ROOT
from src.storage import match_db as db
from src.utils.io import read_json


app = FastAPI(title="CourtFlow API", version="0.1.0")


class MatchOut(BaseModel):
    match_id: str
    court_id: str
    source_type: str
    source_uri: str
    output_dir: str
    state: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    last_error: Optional[str] = None
    created_at: str
    updated_at: str


class ArtifactOut(BaseModel):
    id: int
    match_id: str
    type: str
    path: str
    status: str
    size_bytes: Optional[int] = None
    created_at: str
    updated_at: str


def _landing_path() -> Path:
    """Find landing.html: repo root (from settings) or cwd (for some hosts)."""
    for base in (PROJECT_ROOT, Path.cwd()):
        p = base / "dashboard" / "landing.html"
        if p.exists():
            return p
    return PROJECT_ROOT / "dashboard" / "landing.html"  # fail with clear 404


@app.get("/", tags=["meta"])
def root() -> FileResponse:
    """Main page: enter match ID to open the dashboard."""
    path = _landing_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="landing.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.get("/view", tags=["ui"])
def view_dashboard() -> FileResponse:
    """
    User dashboard: one URL. Open with ?match_id=xxx and optional ?court_id=xxx.
    Example: /view?match_id=match_2026_02_25_022906
    """
    path = PROJECT_ROOT / "dashboard" / "view.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="view.html not found")
    return FileResponse(path, media_type="text/html")


@app.get("/matches", response_model=List[MatchOut], tags=["matches"])
def list_matches(limit: int = 100) -> List[MatchOut]:
    rows = db.list_matches(limit=limit)
    if rows:
        return [MatchOut(**r) for r in rows]
    # Deployed without DB: list match IDs from R2 (matches uploaded to cloud)
    if _r2_configured():
        import os
        from src.cloud.storage_r2 import list_match_ids_from_r2
        from src.utils.time import utcnow_iso
        bucket = os.getenv("R2_BUCKET")
        if bucket:
            ids = list_match_ids_from_r2(bucket, max_keys=limit * 5)[:limit]
            now = utcnow_iso()
            return [
                MatchOut(
                    match_id=mid,
                    court_id="—",
                    source_type="FILE",
                    source_uri="",
                    output_dir="",
                    state="DONE",
                    started_at=None,
                    ended_at=None,
                    last_error=None,
                    created_at=now,
                    updated_at=now,
                )
                for mid in ids
            ]
    return []


def _match_from_r2(match_id: str) -> Optional[MatchOut]:
    """If R2 is configured and report exists for match_id, return minimal MatchOut for deployed (stateless) mode."""
    if not _r2_configured():
        return None
    from src.cloud.upload import get_report_from_r2
    report = get_report_from_r2(match_id)
    if not report:
        return None
    from src.utils.time import utcnow_iso
    now = utcnow_iso()
    return MatchOut(
        match_id=match_id,
        court_id=report.get("court_id") or "—",
        source_type="FILE",
        source_uri="",
        output_dir="",
        state="DONE",
        started_at=None,
        ended_at=None,
        last_error=None,
        created_at=report.get("generated_at") or now,
        updated_at=now,
    )


@app.get("/matches/{match_id}", response_model=MatchOut, tags=["matches"])
def get_match(match_id: str) -> MatchOut:
    row = db.get_match(match_id)
    if row:
        return MatchOut(**row)
    # Deployed without DB: try R2 (report exists => match is "known")
    match_out = _match_from_r2(match_id)
    if match_out:
        return match_out
    raise HTTPException(status_code=404, detail="Match not found")


@app.get("/matches/{match_id}/artifacts", response_model=List[ArtifactOut], tags=["artifacts"])
def list_match_artifacts(match_id: str) -> List[ArtifactOut]:
    if not db.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match not found")
    return [ArtifactOut(**r) for r in db.list_artifacts(match_id)]


@app.get("/matches/{match_id}/report", tags=["reports"])
def get_match_report(match_id: str) -> dict:
    row = db.get_match(match_id)
    if row:
        report_path = Path(row["output_dir"]) / "reports" / "report.json"
        if report_path.exists():
            return read_json(report_path)
    # Deployed without local data: try R2
    if _r2_configured():
        from src.cloud.upload import get_report_from_r2
        report = get_report_from_r2(match_id)
        if report:
            return report
    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/matches/{match_id}/report/heatmap", tags=["reports"])
def get_match_report_heatmap(match_id: str):
    """Serve court heatmap image for the user dashboard. 404 if not generated."""
    row = db.get_match(match_id)
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")
    heatmap_path = Path(row["output_dir"]) / "reports" / "heatmap.png"
    if not heatmap_path.exists():
        raise HTTPException(status_code=404, detail="Heatmap not found")
    return FileResponse(heatmap_path, media_type="image/png")


@app.get("/matches/{match_id}/highlights/video", tags=["reports"])
def get_match_highlights_video(match_id: str):
    """Serve highlights.mp4 for the user dashboard (local only; use cloud/urls when deployed)."""
    row = db.get_match(match_id)
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")
    video_path = Path(row["output_dir"]) / "highlights" / "highlights.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Highlights video not found")
    return FileResponse(video_path, media_type="video/mp4")


@app.get("/matches/{match_id}/meta", tags=["reports"])
def get_match_meta(match_id: str) -> dict:
    row = db.get_match(match_id)
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")
    meta_path = Path(row["output_dir"]) / "meta" / "meta.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Meta not found")
    return read_json(meta_path)


# ---- Cloud (R2) ----

def _r2_configured() -> bool:
    import os
    return bool(
        os.getenv("R2_ACCESS_KEY_ID")
        and os.getenv("R2_SECRET_ACCESS_KEY")
        and os.getenv("R2_BUCKET")
        and (os.getenv("R2_ACCOUNT_ID") or os.getenv("R2_ENDPOINT_URL"))
    )


@app.get("/matches/{match_id}/cloud/urls", tags=["cloud"])
def get_match_cloud_urls(
    match_id: str,
    expires_seconds: int = 3600,
) -> dict:
    """
    Return presigned URLs for highlights.mp4 and report.json in R2.
    Requires R2 to be configured. Works with or without local DB (for deployed stateless mode).
    """
    if not _r2_configured():
        raise HTTPException(
            status_code=503,
            detail="R2 not configured. Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_ACCOUNT_ID in .env",
        )
    from src.cloud.upload import get_signed_url_for_key
    prefix = f"matches/{match_id}"
    out = {"highlights_url": None, "report_url": None}
    try:
        out["highlights_url"] = get_signed_url_for_key(
            f"{prefix}/highlights.mp4", expiration_seconds=expires_seconds
        )
    except Exception:
        pass
    try:
        out["report_url"] = get_signed_url_for_key(
            f"{prefix}/report.json", expiration_seconds=expires_seconds
        )
    except Exception:
        pass
    return out


@app.post("/matches/{match_id}/cloud/upload", tags=["cloud"])
def post_match_cloud_upload(match_id: str) -> dict:
    """
    Upload this match's highlights.mp4 and report.json to R2.
    Returns keys and presigned URLs when R2 is configured.
    """
    if not db.get_match(match_id):
        raise HTTPException(status_code=404, detail="Match not found")
    if not _r2_configured():
        raise HTTPException(
            status_code=503,
            detail="R2 not configured. Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_ACCOUNT_ID in .env",
        )
    from src.cloud.upload import upload_match_artifacts, get_signed_url_for_key
    result = upload_match_artifacts(match_id)
    # Attach short-lived URLs for convenience
    result["urls"] = {}
    for k in result.get("keys", []):
        try:
            result["urls"][k] = get_signed_url_for_key(k, expiration_seconds=3600)
        except Exception:
            result["urls"][k] = None
    return result
