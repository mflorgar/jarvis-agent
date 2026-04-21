"""LLM wrapper with a rule-based mock that still does tool calling.

The mock detects keywords in the user message and emits a ToolCall
matching the intent. This lets the entire agent loop run end-to-end
without any external LLM API, which is perfect for demos, tests and CI.

For real usage, swap to anthropic or openai backends via env var.
"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class AIResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def wants_tool(self) -> bool:
        return len(self.tool_calls) > 0


class MockLLM:
    """Keyword-based rule engine that mimics tool-calling behaviour."""

    _TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|h)?", re.IGNORECASE)

    def invoke(self, messages: list[dict], tools: list) -> AIResponse:
        user_msg = self._last_user_message(messages)
        if not user_msg:
            return AIResponse(content="Dime qué necesitas y te ayudo.")

        text = user_msg.lower()

        # Did we already get a tool result? If yes, this turn is a reply.
        if messages and messages[-1].get("role") == "tool":
            return self._final_reply(messages[-1]["content"])

        # -------- Intent: create event (check BEFORE list so "agenda una reunión" wins) --------
        create_keywords = [
            "agendar", "programar", "reunión con", "reunion con",
            "cita con", "meeting con",
            "agenda una", "agenda un", "agenda a", "agenda el",
        ]
        if any(k in text for k in create_keywords):
            title = self._extract_title(user_msg)
            start = self._extract_datetime(user_msg)
            return self._call("create_event", {
                "title": title,
                "start_iso": start.isoformat(timespec="minutes"),
                "duration_minutes": 60,
            })

        # -------- Intent: list agenda / notes / reminders --------
        if any(k in text for k in [
            "mi agenda", "ver agenda", "mostrar agenda", "listar agenda",
            "muéstrame", "muestrame", "mi día", "mi dia",
            "eventos", "próximos eventos",
        ]):
            return self._call("list_agenda", {})
        if any(k in text for k in ["mis notas", "listar notas", "ver notas"]):
            return self._call("list_notes", {})
        if any(k in text for k in ["recordatorios", "pendientes"]):
            return self._call("list_reminders", {})

        # -------- Intent: free slot --------
        if any(k in text for k in ["hueco libre", "slot libre", "hueco", "disponibilidad"]):
            day = self._extract_datetime(user_msg).date().isoformat()
            return self._call("find_free_slot", {"day_iso": day, "duration_minutes": 60})

        # -------- Intent: create reminder --------
        if any(k in text for k in ["recuerdame", "recuérdame", "recordarme", "recordatorio"]):
            due = self._extract_datetime(user_msg)
            return self._call("create_reminder", {
                "text": user_msg,
                "due_at_iso": due.isoformat(timespec="minutes"),
            })

        # -------- Intent: create note --------
        if any(k in text for k in ["nota:", "apunta", "anota", "guarda esta nota"]):
            content = re.sub(r"^(anota|apunta|nota:|guarda esta nota:?)\s*", "",
                             user_msg, flags=re.IGNORECASE).strip()
            return self._call("create_note", {"content": content, "tag": ""})
        if text.startswith("busca nota") or "buscar nota" in text:
            query = re.sub(r"^(busca nota|buscar nota)[s]?\s*(sobre|de)?\s*",
                           "", user_msg, flags=re.IGNORECASE).strip()
            return self._call("search_notes", {"query": query or user_msg})

        # -------- Intent: code --------
        if "revisa" in text and ("código" in text or "codigo" in text or "code" in text):
            snippet = self._extract_code(user_msg)
            return self._call("review_code", {"code": snippet or user_msg})
        if "explica" in text and ("código" in text or "codigo" in text or "code" in text):
            snippet = self._extract_code(user_msg)
            return self._call("explain_code", {"code": snippet or user_msg})
        if any(k in text for k in ["genera código", "genera codigo", "snippet", "ejemplo de código"]):
            return self._call("generate_code_snippet", {
                "description": user_msg, "language": "python",
            })

        # -------- Fallback: chat --------
        return AIResponse(content=(
            "Puedo ayudarte con agenda (crear eventos, listar agenda, huecos libres), "
            "notas y recordatorios, y revisión o generación de código. "
            "¿Qué te gustaría hacer?"
        ))

    # ---- Helpers --------------------------------------------------

    def _last_user_message(self, messages: list[dict]) -> str:
        for m in reversed(messages):
            if m.get("role") == "user":
                return m.get("content", "")
        return ""

    def _call(self, name: str, args: dict) -> AIResponse:
        return AIResponse(
            tool_calls=[ToolCall(id=str(uuid.uuid4()), name=name, args=args)]
        )

    def _final_reply(self, tool_output: str) -> AIResponse:
        return AIResponse(content=f"Listo. {tool_output}")

    def _extract_title(self, text: str) -> str:
        match = re.search(
            r"(?:reuni[óo]n|reunion|cita|meeting)\s+(?:con|de|para)\s+(.+?)(?:\s+(?:el|ma[ñn]ana|hoy|a las|\d).*|$)",
            text, flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().rstrip(".,")
        return "Nuevo evento"

    def _extract_datetime(self, text: str) -> datetime:
        base = datetime.utcnow().replace(second=0, microsecond=0)
        if "mañana" in text.lower() or "manana" in text.lower():
            base = base + timedelta(days=1)
        match = self._TIME_RE.search(text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            period = (match.group(3) or "").lower()
            if period == "pm" and hour < 12:
                hour += 12
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                base = base.replace(hour=hour, minute=minute)
        else:
            base = base.replace(hour=10, minute=0)
        return base

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```(?:\w+)?\n(.*?)```", text, flags=re.DOTALL)
        if match:
            return match.group(1)
        return ""


class LLMClient:
    """Facade. Resolves provider from env var at construction."""

    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()
        self._backend = self._build_backend()

    def _build_backend(self):
        # Real providers would implement the same `invoke(messages, tools) -> AIResponse`
        # interface. Kept out of the MVP to keep the repo dependency-free.
        return MockLLM()

    def invoke(self, messages: list[dict], tools: list) -> AIResponse:
        return self._backend.invoke(messages, tools)
