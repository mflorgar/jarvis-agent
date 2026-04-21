"""Calendar and agenda skills exposed as LangChain StructuredTools."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from langchain_core.tools import StructuredTool

from src.memory import Storage


def build_calendar_tools(storage: Storage) -> List[StructuredTool]:
    def _create_event(
        title: str, start_iso: str, duration_minutes: int = 60, attendees: str = "",
    ) -> str:
        try:
            start = datetime.fromisoformat(start_iso)
        except ValueError:
            return f"Invalid ISO datetime: {start_iso}. Use YYYY-MM-DDTHH:MM."
        end = start + timedelta(minutes=duration_minutes)
        event = storage.add_event(title=title, start=start, end=end, attendees=attendees)
        return (
            f"Event #{event.id} '{title}' created "
            f"{start.isoformat(timespec='minutes')} → {end.isoformat(timespec='minutes')}."
        )

    def _list_agenda(start_from_iso: str = "") -> str:
        start_from = None
        if start_from_iso:
            try:
                start_from = datetime.fromisoformat(start_from_iso)
            except ValueError:
                return f"Invalid ISO datetime: {start_from_iso}."
        events = storage.list_events(start_from=start_from)
        if not events:
            return "No upcoming events."
        return "\n".join(
            f"#{e.id} {e.start.isoformat(timespec='minutes')} — {e.title}"
            + (f" (with {e.attendees})" if e.attendees else "")
            for e in events
        )

    def _find_free_slot(day_iso: str, duration_minutes: int = 60) -> str:
        try:
            day = datetime.fromisoformat(day_iso)
        except ValueError:
            return f"Invalid ISO date: {day_iso}. Use YYYY-MM-DD."
        slot = storage.find_free_slot(day=day, duration_minutes=duration_minutes)
        if slot is None:
            return f"No free slot of {duration_minutes} min on {day.date()}."
        return f"Free slot available on {slot.isoformat(timespec='minutes')}."

    return [
        StructuredTool.from_function(
            func=_create_event,
            name="create_event",
            description=(
                "Create a calendar event. title, start_iso (ISO 8601), "
                "duration_minutes (int, default 60), attendees (comma-separated)."
            ),
        ),
        StructuredTool.from_function(
            func=_list_agenda,
            name="list_agenda",
            description="List upcoming calendar events, optionally from a start time.",
        ),
        StructuredTool.from_function(
            func=_find_free_slot,
            name="find_free_slot",
            description="Find the first free slot on a given day (09:00–18:00).",
        ),
    ]
