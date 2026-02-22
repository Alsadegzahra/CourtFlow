from __future__ import annotations
from pathlib import Path
import os

# src/common/config.py -> src/common -> src -> PROJECT_ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.getenv("COURTFLOW_DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.getenv("COURTFLOW_DB_PATH", DATA_DIR / "courtflow.db"))

INPUT_VIDEOS_DIR = DATA_DIR / "input_videos"
OUTPUTS_DIR = DATA_DIR / "outputs"

def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)