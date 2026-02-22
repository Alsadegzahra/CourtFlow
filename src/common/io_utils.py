import json
from pathlib import Path
from typing import Any, Dict, List
from typing import Optional

def ensure_dir(path: Path) -> None:
    """
    Create a directory if it doesn't exist.
    Safe for nested paths.
    """
    path.mkdir(parents=True, exist_ok=True)


def file_exists(path: Path) -> bool:
    """
    Check if file exists.
    """
    return path.exists()


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Write dictionary data to a JSON file.
    Automatically creates parent folders if needed.
    """
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """
    Safer JSON write (prevents corrupted files if process crashes).
    Writes to temp file then replaces original.
    """
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    tmp_path.replace(path)


def read_json(path: Path) -> Dict[str, Any]:
    """
    Read JSON file and return dictionary.
    """
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, content: str) -> None:
    """
    Write plain text to file.
    """
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")

def list_files(path: Path, suffix: Optional[str] = None) -> List[Path]:
    """
    List files in directory.
    Optionally filter by suffix (e.g. '.mp4')
    """
    if not path.exists():
        return []

    files = [p for p in path.iterdir() if p.is_file()]
    if suffix:
        files = [p for p in files if p.suffix == suffix]

    return files