"""
Per-match tracks SQLite: create schema, batch insert tracks, query helpers.
Option C: one tracks.db per match at data/matches/<match_id>/tracks/tracks.db
Uses: sqlite3, utils/time
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List

# TODO: define schema (frame, timestamp, player_id, x_pixel, y_pixel, x_court, y_court, bbox_xyxy?)
# TODO: create_db(path), insert_tracks_batch(conn, rows), query_by_frame, etc.

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tracks (
    frame INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    player_id INTEGER NOT NULL,
    x_pixel REAL NOT NULL,
    y_pixel REAL NOT NULL,
    x_court REAL,
    y_court REAL,
    bbox_xyxy TEXT,
    PRIMARY KEY (frame, player_id)
);
CREATE INDEX IF NOT EXISTS idx_tracks_frame ON tracks(frame);
"""


def create_tracks_db(db_path: Path) -> None:
    """Create tracks.db and schema for a match."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(_SCHEMA_SQL)


def insert_tracks_batch(db_path: Path, rows: List[Dict[str, Any]]) -> None:
    """Batch insert track rows. Each row: frame, timestamp, player_id, x_pixel, y_pixel, x_court?, y_court?, bbox_xyxy?."""
    # TODO: implement
    raise NotImplementedError("tracks_db insert not implemented yet; pipeline still uses tracks.json")
