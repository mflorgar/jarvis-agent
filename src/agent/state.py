"""Typed state for the Jarvis agent graph."""

from __future__ import annotations

from typing import TypedDict


class Message(TypedDict, total=False):
    role: str        # "user" | "assistant" | "tool"
    content: str
    tool_name: str


class AgentState(TypedDict, total=False):
    messages: list[Message]
    last_response: str
    pending_tool: dict | None
    iterations: int
