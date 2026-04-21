"""Notes and reminders skills exposed as LangChain StructuredTools."""

from __future__ import annotations

from datetime import datetime
from typing import List

from langchain_core.tools import StructuredTool

from src.memory import Storage


def build_notes_tools(storage: Storage) -> List[StructuredTool]:
    def _create_note(content: str, tag: str = "") -> str:
        note = storage.add_note(content=content, tag=tag)
        return f"Note #{note.id} created with tag '{note.tag or 'none'}'."

    def _list_notes(tag: str = "") -> str:
        notes = storage.list_notes(tag=tag or None)
        if not notes:
            return "No notes found."
        return "\n".join(
            f"#{n.id} [{n.tag or 'none'}] {n.content}" for n in notes
        )

    def _search_notes(query: str) -> str:
        notes = storage.search_notes(query)
        if not notes:
            return f"No notes matching '{query}'."
        return "\n".join(f"#{n.id} {n.content}" for n in notes)

    def _create_reminder(text: str, due_at_iso: str) -> str:
        try:
            due = datetime.fromisoformat(due_at_iso)
        except ValueError:
            return f"Invalid ISO datetime: {due_at_iso}. Use YYYY-MM-DDTHH:MM."
        reminder = storage.add_reminder(text=text, due_at=due)
        return f"Reminder #{reminder.id} set for {due.isoformat(timespec='minutes')}."

    def _list_reminders() -> str:
        reminders = storage.list_reminders()
        if not reminders:
            return "No pending reminders."
        return "\n".join(
            f"#{r.id} due {r.due_at.isoformat(timespec='minutes')} — {r.text}"
            for r in reminders
        )

    return [
        StructuredTool.from_function(
            func=_create_note,
            name="create_note",
            description="Save a text note with an optional tag.",
        ),
        StructuredTool.from_function(
            func=_list_notes,
            name="list_notes",
            description="List recent notes. Optional tag to filter.",
        ),
        StructuredTool.from_function(
            func=_search_notes,
            name="search_notes",
            description="Search notes by substring.",
        ),
        StructuredTool.from_function(
            func=_create_reminder,
            name="create_reminder",
            description=(
                "Create a reminder at a future date/time. "
                "due_at_iso must be ISO 8601 like 2026-05-01T10:00."
            ),
        ),
        StructuredTool.from_function(
            func=_list_reminders,
            name="list_reminders",
            description="List pending reminders sorted by due date.",
        ),
    ]
