# src/b2_storage/match_store.py
from __future__ import annotations

from pathlib import Path
from typing import Union

from src.common.config import OUTPUTS_DIR

PathLike = Union[str, Path]

MATCH_SUBDIRS = [
    "raw/chunks",
    "raw/merged",
    "meta",
    "logs",
    "calibration",
    "tracks",
    "highlights",
    "renders",
    "reports",
]


def match_output_dir(match_id: str) -> Path:
    """
    Canonical output dir for a match.
    data/outputs/<match_id>/
    """
    return OUTPUTS_DIR / match_id


def ensure_match_dirs(output_dir: PathLike) -> None:
    """
    Create standard directory structure for a match output folder.
    """
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)
    for sub in MATCH_SUBDIRS:
        (base / sub).mkdir(parents=True, exist_ok=True)


def raw_chunks_dir(output_dir: PathLike) -> Path:
    return Path(output_dir) / "raw" / "chunks"


def raw_merged_dir(output_dir: PathLike) -> Path:
    return Path(output_dir) / "raw" / "merged"


def highlights_dir(output_dir: PathLike) -> Path:
    return Path(output_dir) / "highlights"


def highlights_mp4_path(output_dir: PathLike) -> Path:
    """
    Canonical highlights output path.
    """
    return highlights_dir(output_dir) / "highlights.mp4"


def logs_dir(output_dir: PathLike) -> Path:
    return Path(output_dir) / "logs"