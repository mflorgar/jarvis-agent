"""Skill catalog exposed as LangChain tools."""

from .calendar_skills import build_calendar_tools
from .notes_skills import build_notes_tools
from .code_skills import build_code_tools


def build_all_tools(storage):
    """Return every skill bound to the given storage instance."""
    return [
        *build_calendar_tools(storage),
        *build_notes_tools(storage),
        *build_code_tools(),
    ]


__all__ = [
    "build_all_tools",
    "build_calendar_tools",
    "build_notes_tools",
    "build_code_tools",
]
