from __future__ import annotations

"""
Blob storage backends.

This file provides concrete BlobStorage implementations for local development
and a placeholder for a future Cloudflare R2-backed storage class used by
the upload helpers in b8_cloud_upload.
"""

from dataclasses import dataclass
from pathlib import Path

from src.b8_cloud_upload.uploader import BlobStorage


@dataclass
class LocalBlobStorage(BlobStorage):
    """
    TODO(B9 storage team): this is a simple baseline implementation.

    Use this in local/dev environments where artifacts live on disk and you only
    need a stable URL/path format for dashboards to consume.
    """

    base_dir: Path

    def put_object(self, key: str, file_path: Path) -> str:
        target_path = self.base_dir / key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # NOTE: For local dev we can simply copy the file. In cloud envs this
        # method should instead call the Cloudflare R2 SDK / API.
        target_path.write_bytes(file_path.read_bytes())
        return str(target_path)


@dataclass
class R2BlobStorage(BlobStorage):
    """
    TODO(B9 storage team): implement Cloudflare R2-backed storage.

    This class should:
    - Use R2 credentials/bucket names from environment variables or config.
    - Implement `put_object` to upload data to R2 and return a public or signed URL.
    """

    bucket_name: str

    def put_object(self, key: str, file_path: Path) -> str:
        raise NotImplementedError("R2-backed BlobStorage is not implemented yet.")

