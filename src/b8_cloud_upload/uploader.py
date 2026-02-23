from __future__ import annotations

"""
Cloud upload module.

This file defines the generic BlobStorage protocol and a helper for uploading
artifacts produced by the pipeline. Concrete implementations (local disk,
Cloudflare R2, etc.) live in the b9_cloud_storage package.
"""

from pathlib import Path
from typing import Protocol

from src.domain.models import Artifact


class BlobStorage(Protocol):
    """
    TODO(B8/B9 cloud teams): provide concrete implementations for local disk and Cloudflare R2.

    This interface is intentionally minimal; extend it if you discover new needs.
    """

    def put_object(self, key: str, file_path: Path) -> str:
        """
        Upload `file_path` to object storage under `key`.

        Returns a URL or path string that can be stored in the DB or used by dashboards.
        """
        ...


def upload_artifact_via_storage(
    artifact: Artifact,
    storage: BlobStorage,
) -> str:
    """
    TODO(B8 cloud upload team): call this from the controller/pipeline when an artifact is READY.

    Expected behavior once wired:
    - Use `artifact.path` as the local file to upload.
    - Derive an object key from match id + artifact type + filename.
    - Call `storage.put_object(...)` and return the resulting URL.
    - Optionally: update the artifact record in the DB with the cloud URL.
    """
    local_path = Path(artifact.path)
    key = f"{artifact.match_id}/{artifact.type}/{local_path.name}"
    return storage.put_object(key, local_path)

