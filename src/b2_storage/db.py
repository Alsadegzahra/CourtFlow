# src/b2_storage/db.py
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = "data/courtflow.db"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db_path() -> str:
    return os.getenv("COURTFLOW_DB_PATH", DEFAULT_DB_PATH)


_DB_INITIALIZED = False


def connect() -> sqlite3.Connection:
    """
    Returns a sqlite connection with WAL + foreign keys enabled.
    Also ensures schema exists (init_db) once per process.
    """
    global _DB_INITIALIZED

    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    if not _DB_INITIALIZED:
        # Safe to run repeatedly; tables are IF NOT EXISTS
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
        _DB_INITIALIZED = True

    return conn


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS courts (
    court_id TEXT PRIMARY KEY,
    site_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    court_id TEXT NOT NULL,
    source_type TEXT NOT NULL,   -- FILE, RTSP
    source_uri  TEXT NOT NULL,   -- path or rtsp url
    output_dir  TEXT NOT NULL,

    state       TEXT NOT NULL,   -- CREATED, RECORDING, FINALIZING, FINALIZED, PROCESSING, DONE, FAILED
    started_at  TEXT,
    ended_at    TEXT,
    last_error  TEXT,

    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,

    FOREIGN KEY (court_id) REFERENCES courts(court_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    type TEXT NOT NULL,          -- RAW_CHUNK, RAW_MERGED, HIGHLIGHTS_MP4, ...
    path TEXT NOT NULL,
    status TEXT NOT NULL,        -- WRITING, READY, FAILED
    size_bytes INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_state ON matches(state);
CREATE INDEX IF NOT EXISTS idx_artifacts_match ON artifacts(match_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
"""


def init_db() -> None:
    """
    Kept for compatibility; connect() already ensures schema.
    """
    with connect() as conn:
        conn.execute("SELECT 1")  # touch connection


def upsert_court(court_id: str, site_name: Optional[str] = None) -> None:
    now = utcnow_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO courts (court_id, site_name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(court_id) DO UPDATE SET
                site_name = COALESCE(excluded.site_name, courts.site_name),
                updated_at = excluded.updated_at
            """,
            (court_id, site_name, now, now),
        )


def create_match(
    match_id: str,
    court_id: str,
    source_type: str,
    source_uri: str,
    output_dir: str,
) -> None:
    now = utcnow_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO matches
              (match_id, court_id, source_type, source_uri, output_dir, state, created_at, updated_at)
            VALUES
              (?, ?, ?, ?, ?, 'CREATED', ?, ?)
            """,
            (match_id, court_id, source_type, source_uri, output_dir, now, now),
        )


def ensure_match(
    match_id: str,
    court_id: str,
    source_type: str,
    source_uri: str,
    output_dir: str,
) -> None:
    """
    Creates the match if missing. If it exists, does nothing.
    Useful for reruns in MVP.
    """
    if get_match(match_id) is not None:
        return
    create_match(match_id, court_id, source_type, source_uri, output_dir)


def update_match(
    match_id: str,
    *,
    state: Optional[str] = None,
    started_at: Optional[str] = None,
    ended_at: Optional[str] = None,
    last_error: Optional[str] = None,
) -> None:
    now = utcnow_iso()
    fields = []
    values: List[Any] = []

    if state is not None:
        fields.append("state=?")
        values.append(state)
    if started_at is not None:
        fields.append("started_at=?")
        values.append(started_at)
    if ended_at is not None:
        fields.append("ended_at=?")
        values.append(ended_at)
    if last_error is not None:
        fields.append("last_error=?")
        values.append(last_error)

    fields.append("updated_at=?")
    values.append(now)

    values.append(match_id)

    with connect() as conn:
        conn.execute(
            f"UPDATE matches SET {', '.join(fields)} WHERE match_id=?",
            tuple(values),
        )


def add_artifact(
    match_id: str,
    type_: str,
    path: str,
    *,
    status: str = "READY",
    size_bytes: Optional[int] = None,
) -> None:
    now = utcnow_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (match_id, type, path, status, size_bytes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (match_id, type_, path, status, size_bytes, now, now),
        )


def list_matches(limit: int = 100) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM matches ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_matches_by_state(state: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM matches WHERE state=? ORDER BY created_at ASC",
            (state,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_match(match_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
    return dict(row) if row else None


def list_artifacts(match_id: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE match_id=? ORDER BY created_at DESC",
            (match_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_latest_artifact(match_id: str, type_: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM artifacts
            WHERE match_id=? AND type=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (match_id, type_),
        ).fetchone()
    return dict(row) if row else None