"""
Load CourtConfig by court_id; list available courts.
Uses: utils/io, court/config
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from src.config.settings import COURTS_DIR
from src.court.config import CourtConfig
from src.utils.io import read_json


def list_court_ids() -> List[str]:
    """List court_id from data/courts/ subdirs."""
    if not COURTS_DIR.exists():
        return []
    return [d.name for d in COURTS_DIR.iterdir() if d.is_dir()]


def load_court_config(court_id: str) -> Optional[CourtConfig]:
    """Load CourtConfig from data/courts/<court_id>/court_config.json."""
    path = COURTS_DIR / court_id / "court_config.json"
    if not path.exists():
        return None
    data = read_json(path)
    return CourtConfig(**data)
