"""SQLite-backed storage for notes, reminders, events and conversation log.

Single file, stdlib only, thread-safe via per-call connections. The
schema is created on first access so the DB file can be deleted and
regenerated freely.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tag TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    due_at TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    attendees TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass
class Note:
    id: int
    content: str
    tag: str
    created_at: datetime


@dataclass
class Reminder:
    id: int
    text: str
    due_at: datetime
    done: bool
    created_at: datetime


@dataclass
class Event:
    id: int
    title: str
    start: datetime
    end: datetime
    attendees: str
    created_at: datetime


class Storage:
    """Thin wrapper over sqlite3 for the Jarvis agent's long-term memory."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path or os.getenv("JARVIS_DB_PATH", "data/jarvis.db"))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ---- Notes -------------------------------------------------------

    def add_note(self, content: str, tag: str = "") -> Note:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO notes (content, tag, created_at) VALUES (?, ?, ?)",
                (content, tag, now),
            )
            return Note(id=cur.lastrowid, content=content, tag=tag, created_at=datetime.fromisoformat(now))

    def list_notes(self, tag: str | None = None, limit: int = 20) -> list[Note]:
        with self._conn() as conn:
            if tag:
                rows = conn.execute(
                    "SELECT * FROM notes WHERE tag = ? ORDER BY id DESC LIMIT ?",
                    (tag, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
        return [
            Note(id=r["id"], content=r["content"], tag=r["tag"],
                 created_at=datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]

    def search_notes(self, query: str, limit: int = 10) -> list[Note]:
        pattern = f"%{query}%"
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM notes WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                (pattern, limit),
            ).fetchall()
        return [
            Note(id=r["id"], content=r["content"], tag=r["tag"],
                 created_at=datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]

    # ---- Reminders ---------------------------------------------------

    def add_reminder(self, text: str, due_at: datetime) -> Reminder:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO reminders (text, due_at, done, created_at) VALUES (?, ?, 0, ?)",
                (text, due_at.isoformat(), now),
            )
            return Reminder(
                id=cur.lastrowid, text=text, due_at=due_at,
                done=False, created_at=datetime.fromisoformat(now),
            )

    def list_reminders(self, include_done: bool = False, limit: int = 20) -> list[Reminder]:
        with self._conn() as conn:
            if include_done:
                rows = conn.execute(
                    "SELECT * FROM reminders ORDER BY due_at ASC LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM reminders WHERE done = 0 ORDER BY due_at ASC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            Reminder(
                id=r["id"], text=r["text"],
                due_at=datetime.fromisoformat(r["due_at"]),
                done=bool(r["done"]),
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    def mark_reminder_done(self, reminder_id: int) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "UPDATE reminders SET done = 1 WHERE id = ?", (reminder_id,)
            )
            return cur.rowcount > 0

    # ---- Events ------------------------------------------------------

    def add_event(
        self, title: str, start: datetime, end: datetime, attendees: str = ""
    ) -> Event:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO events (title, start, end, attendees, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, start.isoformat(), end.isoformat(), attendees, now),
            )
            return Event(
                id=cur.lastrowid, title=title, start=start, end=end,
                attendees=attendees, created_at=datetime.fromisoformat(now),
            )

    def list_events(
        self, start_from: datetime | None = None, limit: int = 20
    ) -> list[Event]:
        with self._conn() as conn:
            if start_from:
                rows = conn.execute(
                    "SELECT * FROM events WHERE start >= ? ORDER BY start ASC LIMIT ?",
                    (start_from.isoformat(), limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY start ASC LIMIT ?", (limit,)
                ).fetchall()
        return [
            Event(
                id=r["id"], title=r["title"],
                start=datetime.fromisoformat(r["start"]),
                end=datetime.fromisoformat(r["end"]),
                attendees=r["attendees"] or "",
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    def find_free_slot(
        self, day: datetime, duration_minutes: int = 60,
        day_start_hour: int = 9, day_end_hour: int = 18,
    ) -> datetime | None:
        """Return the first free slot of the given duration on the given day."""
        from datetime import timedelta

        start_of_day = day.replace(hour=day_start_hour, minute=0, second=0, microsecond=0)
        end_of_day = day.replace(hour=day_end_hour, minute=0, second=0, microsecond=0)

        # Fetch events overlapping that day.
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT start, end FROM events WHERE start >= ? AND start < ? ORDER BY start",
                (start_of_day.isoformat(), end_of_day.isoformat()),
            ).fetchall()
        events = [(datetime.fromisoformat(r["start"]), datetime.fromisoformat(r["end"])) for r in rows]

        cursor = start_of_day
        for ev_start, ev_end in events:
            if (ev_start - cursor) >= timedelta(minutes=duration_minutes):
                return cursor
            cursor = max(cursor, ev_end)
        if (end_of_day - cursor) >= timedelta(minutes=duration_minutes):
            return cursor
        return None

    # ---- Conversation log -------------------------------------------

    def log_message(self, role: str, content: str) -> None:
        now = datetime.utcnow().isoformat(timespec="seconds")
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO conversation (role, content, created_at) VALUES (?, ?, ?)",
                (role, content, now),
            )

    def recent_conversation(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content, created_at FROM conversation "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]
