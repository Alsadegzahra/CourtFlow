import json
from pathlib import Path
from typing import Any, Dict


def ensure_dir(path: Path) -> None:
    """
    Create a directory if it doesn't exist.
    Safe for nested paths.
    """
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Write dictionary data to a JSON file.
    Automatically creates parent folders if needed.
    """
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_json(path: Path) -> Dict[str, Any]:
    """
    Read JSON file and return dictionary.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
