"""Tests for the skill tools."""

from __future__ import annotations

from src.skills import build_all_tools


def test_all_tools_built(storage):
    tools = build_all_tools(storage)
    names = {t.name for t in tools}
    assert {"create_event", "list_agenda", "find_free_slot"}.issubset(names)
    assert {"create_note", "list_notes", "search_notes",
            "create_reminder", "list_reminders"}.issubset(names)
    assert {"explain_code", "review_code", "generate_code_snippet"}.issubset(names)


def test_review_code_detects_bare_except(storage):
    tools = {t.name: t for t in build_all_tools(storage)}
    output = tools["review_code"].invoke({"code": "try:\n    pass\nexcept:\n    pass\n"})
    assert "bare" in output.lower() or "except" in output.lower()


def test_explain_code_counts_structures(storage):
    tools = {t.name: t for t in build_all_tools(storage)}
    output = tools["explain_code"].invoke({
        "code": "def foo():\n    pass\n\nclass Bar:\n    pass\n",
    })
    assert "function" in output.lower()
    assert "class" in output.lower()


def test_generate_snippet_fastapi(storage):
    tools = {t.name: t for t in build_all_tools(storage)}
    output = tools["generate_code_snippet"].invoke({
        "description": "fastapi endpoint", "language": "python",
    })
    assert "FastAPI" in output
