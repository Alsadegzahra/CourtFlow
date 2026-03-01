"""
Upload reports/highlights (and optionally tracks) to Cloudflare R2.
Uses: cloud/storage_r2, config/settings, pipeline/paths.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from src.config.settings import MATCHES_DIR


def upload_artifact(
    key: str,
    file_path: Path,
    *,
    bucket: Optional[str] = None,
) -> str:
    """
    Upload a single file to R2 under `key`. Returns the key.
    Requires R2_* env vars (see .env.example).
    """
    from src.cloud.storage_r2 import upload_file
    return upload_file(file_path, key=key, bucket=bucket)


def upload_match_artifacts(
    match_id: str,
    *,
    upload_highlights_mp4: bool = True,
    upload_report: bool = True,
    upload_heatmap: bool = True,
    bucket: Optional[str] = None,
) -> dict:
    """
    Upload highlights.mp4, report.json, and heatmap.png for a match to R2.
    Returns dict with keys used. Dashboard uses heatmap_url from cloud/urls when deployed.
    """
    base = MATCHES_DIR / match_id
    if not base.exists():
        raise FileNotFoundError(f"Match dir not found: {base}")

    prefix = f"matches/{match_id}"
    result: dict = {"keys": []}

    if upload_highlights_mp4:
        hp = base / "highlights" / "highlights.mp4"
        if hp.exists():
            key = f"{prefix}/highlights.mp4"
            upload_artifact(key, hp, bucket=bucket)
            result["keys"].append(key)
            result["highlights_key"] = key

    if upload_report:
        rp = base / "reports" / "report.json"
        if rp.exists():
            key = f"{prefix}/report.json"
            upload_artifact(key, rp, bucket=bucket)
            result["keys"].append(key)
            result["report_key"] = key

    if upload_heatmap:
        heatmap_path = base / "reports" / "heatmap.png"
        if heatmap_path.exists():
            key = f"{prefix}/heatmap.png"
            upload_artifact(key, heatmap_path, bucket=bucket)
            result["keys"].append(key)
            result["heatmap_key"] = key

    return result


def get_signed_url_for_key(key: str, expiration_seconds: int = 3600) -> str:
    """Return a presigned URL for an R2 object (for dashboard/API to serve links)."""
    from src.cloud.storage_r2 import get_signed_url
    bucket = os.getenv("R2_BUCKET")
    if not bucket:
        raise RuntimeError("Set R2_BUCKET in .env")
    return get_signed_url(bucket, key, expiration_seconds=expiration_seconds)


def get_report_from_r2(match_id: str, *, bucket: Optional[str] = None) -> Optional[dict]:
    """
    Fetch report.json for a match from R2. Returns None if R2 not configured or key missing.
    Used by deployed API when local filesystem has no match data.
    """
    import json
    bucket = bucket or os.getenv("R2_BUCKET")
    if not bucket:
        return None
    try:
        from src.cloud.storage_r2 import get_object_bytes
        key = f"matches/{match_id}/report.json"
        raw = get_object_bytes(bucket, key)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None
