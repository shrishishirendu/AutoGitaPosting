from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Iterable


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            error TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            type TEXT NOT NULL,
            path TEXT NOT NULL,
            hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            caption TEXT NOT NULL,
            image_path TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def insert_run(conn: sqlite3.Connection, run_id: str, status: str, started_at: datetime) -> None:
    conn.execute(
        "INSERT INTO runs (run_id, status, started_at) VALUES (?, ?, ?)",
        (run_id, status, started_at.isoformat()),
    )
    conn.commit()


def finish_run(
    conn: sqlite3.Connection,
    run_id: str,
    status: str,
    finished_at: datetime | None,
    error: str | None,
) -> None:
    conn.execute(
        "UPDATE runs SET status = ?, finished_at = ?, error = ? WHERE run_id = ?",
        (status, finished_at.isoformat() if finished_at else None, error, run_id),
    )
    conn.commit()


def add_artifact(
    conn: sqlite3.Connection,
    run_id: str,
    artifact_type: str,
    path: str,
    hash_value: str,
    created_at: datetime,
) -> None:
    conn.execute(
        "INSERT INTO artifacts (run_id, type, path, hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, artifact_type, path, hash_value, created_at.isoformat()),
    )
    conn.commit()


def add_draft(
    conn: sqlite3.Connection,
    run_id: str,
    caption: str,
    image_path: str,
    status: str,
    created_at: datetime,
) -> None:
    conn.execute(
        "INSERT INTO drafts (run_id, caption, image_path, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, caption, image_path, status, created_at.isoformat()),
    )
    conn.commit()


def update_draft_status(conn: sqlite3.Connection, run_id: str, status: str) -> None:
    conn.execute("UPDATE drafts SET status = ? WHERE run_id = ?", (status, run_id))
    conn.commit()


def list_runs(conn: sqlite3.Connection, limit: int) -> Iterable[sqlite3.Row]:
    return conn.execute(
        "SELECT run_id, status, started_at, finished_at, error FROM runs ORDER BY started_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
