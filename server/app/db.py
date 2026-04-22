"""Simple SQLite-backed storage of practice sessions."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DB_PATH = Path(os.environ.get("SESSION_DB_PATH", "sessions.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                song_title  TEXT NOT NULL,
                artist      TEXT,
                user_note   TEXT,
                overall     INTEGER,
                features    TEXT NOT NULL,
                feedback    TEXT NOT NULL,
                comparison  TEXT
            )
            """
        )


def save_session(
    song_title: str,
    artist: str,
    user_note: str,
    features: dict[str, Any],
    feedback: dict[str, Any],
    comparison: dict[str, Any] | None,
) -> int:
    overall = feedback.get("overall_score")
    try:
        overall_int = int(overall) if overall is not None else None
    except (TypeError, ValueError):
        overall_int = None

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions
              (created_at, song_title, artist, user_note, overall, features, feedback, comparison)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                song_title,
                artist,
                user_note,
                overall_int,
                json.dumps(features, ensure_ascii=False),
                json.dumps(feedback, ensure_ascii=False),
                json.dumps(comparison, ensure_ascii=False) if comparison else None,
            ),
        )
        return int(cur.lastrowid)


def list_sessions(limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, song_title, artist, overall
            FROM sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_session(session_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["features"] = json.loads(data["features"])
    data["feedback"] = json.loads(data["feedback"])
    if data.get("comparison"):
        data["comparison"] = json.loads(data["comparison"])
    return data


def delete_session(session_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0
