"""
read/write json, npy, png; safe mkdirs.
Replaces common/io_utils for the new layout.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def read_json(path: Path) -> Any:
    """Load JSON; returns dict or list depending on file content."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic_any(path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
    """Atomic write of JSON (dict or list)."""
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def list_files(path: Path, suffix: Optional[str] = None) -> List[Path]:
    if not path.exists():
        return []
    files = [p for p in path.iterdir() if p.is_file()]
    if suffix:
        files = [p for p in files if p.suffix == suffix]
    return files
