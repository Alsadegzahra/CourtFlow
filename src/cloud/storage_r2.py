"""
Cloudflare R2 client wrapper (S3-compatible API).
Uses: boto3, env vars R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_ACCOUNT_ID (or R2_ENDPOINT_URL).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Optional: only required when cloud upload is enabled
try:
    import boto3
    from botocore.config import Config
except ImportError:
    boto3 = None  # type: ignore


def _get_client():
    if boto3 is None:
        raise RuntimeError("Install boto3 for R2: pip install boto3")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    account_id = os.getenv("R2_ACCOUNT_ID")
    endpoint = os.getenv("R2_ENDPOINT_URL")
    if not endpoint and account_id:
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    if not all([access_key, secret_key, endpoint]):
        raise RuntimeError(
            "Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_ENDPOINT_URL (or R2_ACCOUNT_ID) in .env"
        )
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def put_object(
    bucket: str,
    key: str,
    file_path: Path,
    *,
    content_type: Optional[str] = None,
) -> str:
    """
    Upload a file to R2. Returns the key (use get_signed_url or public URL if bucket is public).
    """
    client = _get_client()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    with open(file_path, "rb") as f:
        client.upload_fileobj(f, bucket, key, ExtraArgs=extra)
    return key


def get_object_bytes(bucket: str, key: str) -> bytes:
    """Download object from R2; raises on missing or error."""
    client = _get_client()
    resp = client.get_object(Bucket=bucket, Key=key)
    return resp["Body"].read()


def list_match_ids_from_r2(bucket: str, *, prefix: str = "matches/", max_keys: int = 200) -> list[str]:
    """
    List object keys under prefix (e.g. matches/) and return unique match_id segments.
    Keys are like matches/match_2026_02_25_022906/report.json -> match_2026_02_25_022906.
    """
    client = _get_client()
    seen: set[str] = set()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys):
        for obj in page.get("Contents") or []:
            key = obj.get("Key") or ""
            parts = key.rstrip("/").split("/")
            if len(parts) >= 2:
                seen.add(parts[1])
    return sorted(seen)


def get_signed_url(
    bucket: str,
    key: str,
    expiration_seconds: int = 3600,
) -> str:
    """Generate a presigned URL for GET. Requires same credentials as put_object."""
    client = _get_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiration_seconds,
    )
    return url


def upload_file(
    file_path: Path,
    *,
    key: Optional[str] = None,
    bucket: Optional[str] = None,
) -> str:
    """
    Upload file to R2. Key defaults to file name; bucket from env R2_BUCKET.
    Returns the object key.
    """
    bucket = bucket or os.getenv("R2_BUCKET")
    if not bucket:
        raise RuntimeError("Set R2_BUCKET in .env")
    k = key or file_path.name
    content_type = "video/mp4" if file_path.suffix.lower() == ".mp4" else None
    put_object(bucket, k, file_path, content_type=content_type)
    return k
