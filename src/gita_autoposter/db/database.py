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
            social_en TEXT,
            professional_en TEXT,
            practical_en TEXT,
            caption_final_en TEXT,
            hashtags TEXT,
            style_notes TEXT,
            fingerprint TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verse_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_number INTEGER NOT NULL,
            verse_number INTEGER NOT NULL,
            ord_index INTEGER NOT NULL UNIQUE,
            UNIQUE (chapter_number, verse_number)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verse_progress (
            id INTEGER PRIMARY KEY,
            next_ord_index INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS verse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_number INTEGER NOT NULL,
            verse_number INTEGER NOT NULL,
            ord_index INTEGER NOT NULL,
            run_id TEXT NOT NULL,
            status TEXT NOT NULL,
            reserved_at TEXT NOT NULL,
            posted_at TEXT
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO verse_progress (id, next_ord_index) VALUES (1, 0)"
    )
    _ensure_draft_columns(conn)
    conn.commit()


def _ensure_draft_columns(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"] for row in conn.execute("PRAGMA table_info(drafts)").fetchall()
    }
    columns = {
        "social_en": "TEXT",
        "professional_en": "TEXT",
        "practical_en": "TEXT",
        "caption_final_en": "TEXT",
        "hashtags": "TEXT",
        "style_notes": "TEXT",
        "fingerprint": "TEXT",
    }
    for name, col_type in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE drafts ADD COLUMN {name} {col_type}")


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
    social_en: str | None = None,
    professional_en: str | None = None,
    practical_en: str | None = None,
    caption_final_en: str | None = None,
    hashtags: str | None = None,
    style_notes: str | None = None,
    fingerprint: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO drafts (run_id, caption, image_path, status, created_at, "
        "social_en, professional_en, practical_en, caption_final_en, hashtags, style_notes, fingerprint) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            caption,
            image_path,
            status,
            created_at.isoformat(),
            social_en,
            professional_en,
            practical_en,
            caption_final_en,
            hashtags,
            style_notes,
            fingerprint,
        ),
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


def get_recent_captions(conn: sqlite3.Connection, limit: int) -> list[str]:
    rows = conn.execute(
        "SELECT caption_final_en FROM drafts WHERE caption_final_en IS NOT NULL "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [row["caption_final_en"] for row in rows]


def get_recent_caption_rows(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT caption_final_en, fingerprint, created_at FROM drafts "
        "WHERE caption_final_en IS NOT NULL ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()


def get_sequence_snapshot(conn: sqlite3.Connection) -> list[tuple[int, int, int]]:
    rows = conn.execute(
        "SELECT chapter_number, verse_number, ord_index FROM verse_queue ORDER BY ord_index"
    ).fetchall()
    return [(row["chapter_number"], row["verse_number"], row["ord_index"]) for row in rows]


def get_queue_pairs(conn: sqlite3.Connection) -> list[tuple[int, int, int]]:
    rows = conn.execute(
        "SELECT chapter_number, verse_number, ord_index FROM verse_queue ORDER BY ord_index"
    ).fetchall()
    return [(row["chapter_number"], row["verse_number"], row["ord_index"]) for row in rows]


def load_sequence(conn: sqlite3.Connection, sequence: list[tuple[int, int]], reset: bool) -> str:
    existing = [(row[0], row[1]) for row in get_sequence_snapshot(conn)]
    if existing == sequence:
        return "unchanged"

    if existing and not reset:
        raise ValueError("Sequence mismatch. Use --reset to reload.")

    conn.execute("BEGIN")
    conn.execute("DELETE FROM verse_queue")
    conn.execute("DELETE FROM verse_history")
    conn.execute("DELETE FROM verse_progress")
    conn.execute("INSERT OR IGNORE INTO verse_progress (id, next_ord_index) VALUES (1, 0)")

    for ord_index, (chapter_number, verse_number) in enumerate(sequence):
        conn.execute(
            "INSERT INTO verse_queue (chapter_number, verse_number, ord_index) VALUES (?, ?, ?)",
            (chapter_number, verse_number, ord_index),
        )
    conn.commit()
    return "reloaded"


def get_upcoming(conn: sqlite3.Connection, limit: int) -> list[tuple[int, int, int]]:
    row = conn.execute("SELECT next_ord_index FROM verse_progress WHERE id = 1").fetchone()
    next_ord = row["next_ord_index"] if row else 0
    rows = conn.execute(
        "SELECT chapter_number, verse_number, ord_index FROM verse_queue "
        "WHERE ord_index >= ? ORDER BY ord_index LIMIT ?",
        (next_ord, limit),
    ).fetchall()
    return [(row["chapter_number"], row["verse_number"], row["ord_index"]) for row in rows]


def get_last_posted(conn: sqlite3.Connection, limit: int) -> list[tuple[int, int, int, str]]:
    rows = conn.execute(
        "SELECT chapter_number, verse_number, ord_index, posted_at "
        "FROM verse_history WHERE status = 'POSTED' "
        "ORDER BY posted_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [
        (row["chapter_number"], row["verse_number"], row["ord_index"], row["posted_at"])
        for row in rows
    ]


def reserve_next_verse(conn: sqlite3.Connection, run_id: str) -> tuple[int, int, int]:
    reserved = conn.execute(
        "SELECT chapter_number, verse_number, ord_index "
        "FROM verse_history WHERE status = 'RESERVED' ORDER BY reserved_at ASC LIMIT 1"
    ).fetchone()
    if reserved:
        return reserved["chapter_number"], reserved["verse_number"], reserved["ord_index"]

    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute("SELECT next_ord_index FROM verse_progress WHERE id = 1").fetchone()
    next_ord = row["next_ord_index"] if row else 0
    verse_row = conn.execute(
        "SELECT chapter_number, verse_number, ord_index FROM verse_queue WHERE ord_index = ?",
        (next_ord,),
    ).fetchone()
    if not verse_row:
        conn.execute("ROLLBACK")
        raise ValueError("No more verses available in the queue.")

    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO verse_history (chapter_number, verse_number, ord_index, run_id, status, reserved_at) "
        "VALUES (?, ?, ?, ?, 'RESERVED', ?)",
        (
            verse_row["chapter_number"],
            verse_row["verse_number"],
            verse_row["ord_index"],
            run_id,
            now,
        ),
    )
    conn.execute(
        "UPDATE verse_progress SET next_ord_index = ?, updated_at = ? WHERE id = 1",
        (next_ord + 1, now),
    )
    conn.commit()
    return verse_row["chapter_number"], verse_row["verse_number"], verse_row["ord_index"]


def mark_verse_posted(conn: sqlite3.Connection, run_id: str) -> int:
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        "UPDATE verse_history SET status = 'POSTED', posted_at = ? "
        "WHERE run_id = ? AND status = 'RESERVED'",
        (now, run_id),
    )
    if cursor.rowcount == 0:
        cursor = conn.execute(
            "UPDATE verse_history SET status = 'POSTED', posted_at = ? "
            "WHERE id = (SELECT id FROM verse_history WHERE status = 'RESERVED' "
            "ORDER BY reserved_at ASC LIMIT 1)",
            (now,),
        )
    conn.commit()
    return cursor.rowcount
