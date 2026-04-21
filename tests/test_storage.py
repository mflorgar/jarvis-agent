"""Tests for the SQLite storage layer."""

from __future__ import annotations

from datetime import datetime, timedelta


def test_notes_roundtrip(storage):
    note = storage.add_note("Comprar café", tag="personal")
    assert note.id > 0
    assert note.tag == "personal"

    recent = storage.list_notes(tag="personal")
    assert len(recent) == 1
    assert recent[0].content == "Comprar café"


def test_notes_search(storage):
    storage.add_note("Idea: landing page con chatbot")
    storage.add_note("Otra cosa", tag="work")
    results = storage.search_notes("landing")
    assert len(results) == 1
    assert "landing" in results[0].content


def test_reminders_roundtrip(storage):
    due = datetime(2026, 5, 1, 10, 0)
    reminder = storage.add_reminder("Enviar informe", due_at=due)
    pending = storage.list_reminders()
    assert len(pending) == 1
    assert pending[0].text == "Enviar informe"

    assert storage.mark_reminder_done(reminder.id) is True
    assert storage.list_reminders() == []


def test_events_and_free_slot(storage):
    day = datetime(2026, 5, 1, 9, 0)
    storage.add_event(
        "Sprint planning",
        start=day.replace(hour=10),
        end=day.replace(hour=11),
    )
    storage.add_event(
        "1:1",
        start=day.replace(hour=14),
        end=day.replace(hour=15),
    )

    agenda = storage.list_events()
    assert len(agenda) == 2

    # First gap at 09:00 → 60 min before the 10:00 event
    slot = storage.find_free_slot(day=day, duration_minutes=60)
    assert slot == day.replace(hour=9, minute=0)
