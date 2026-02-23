## B9 – Cloud Storage Backends

- **Responsibility**: Provide concrete implementations of the `BlobStorage` interface (local filesystem, Cloudflare R2, etc.) for use by B8.
- **Main code**: `storage.py`

### Tools / Libraries

- Local filesystem (`pathlib`) for `LocalBlobStorage`
- _(Planned)_ Cloudflare R2 / S3-compatible client for `R2BlobStorage`

### Models / Intelligence

- _(None — infra glue only.)_

