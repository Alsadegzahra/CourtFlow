"""
Global settings: base data dir, default fps, thresholds, logging.
Uses environment variables with sensible defaults for local dev.
Loads .env from project root when present (so R2_* and COURTFLOW_* are set).
"""
from __future__ import annotations

import os
from pathlib import Path

# PROJECT_ROOT: repo root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Load .env so CLI/API see R2_* and COURTFLOW_* without exporting in shell
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass  # python-dotenv optional; env can be set by shell

DATA_DIR = Path(os.getenv("COURTFLOW_DATA_DIR", str(PROJECT_ROOT / "data")))

# Persistent (once per court)
COURTS_DIR = DATA_DIR / "courts"

# Ephemeral per-match outputs
MATCHES_DIR = DATA_DIR / "matches"

# Legacy: global SQLite for match registry + artifacts (optional; can move to Supabase later)
DB_PATH = Path(os.getenv("COURTFLOW_DB_PATH", str(DATA_DIR / "courtflow.db")))

# Defaults for ingest/pipeline
DEFAULT_FPS = 30
DEFAULT_VIDEO_BITRATE = "8M"
DEFAULT_AUDIO_BITRATE = "128k"

# Logging
LOG_LEVEL = os.getenv("COURTFLOW_LOG_LEVEL", "INFO")


def ensure_dirs() -> None:
    """Create data/courts and data/matches if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COURTS_DIR.mkdir(parents=True, exist_ok=True)
    MATCHES_DIR.mkdir(parents=True, exist_ok=True)
