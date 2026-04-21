"""End-to-end tests for the Jarvis agent graph."""

from __future__ import annotations


def _turn(agent, message: str, history: list[dict] | None = None) -> dict:
    history = history or []
    history.append({"role": "user", "content": message})
    result = agent.invoke({"messages": history, "iterations": 0})
    return {
        "messages": result.get("messages", history),
        "reply": result.get("last_response", ""),
    }


def test_agent_creates_event(agent):
    out = _turn(agent, "Agenda una reunión con el equipo mañana a las 10h")
    assert "Event" in out["reply"] or "evento" in out["reply"].lower()


def test_agent_lists_agenda(agent):
    _turn(agent, "Agenda una reunión con el equipo mañana a las 10h")
    out = _turn(agent, "muéstrame mi agenda")
    assert out["reply"]
    assert "10:00" in out["reply"] or "equipo" in out["reply"].lower() or "Event" in out["reply"]


def test_agent_creates_and_lists_notes(agent):
    _turn(agent, "apunta: probar LangGraph esta semana")
    out = _turn(agent, "mis notas")
    assert "LangGraph" in out["reply"] or "probar" in out["reply"].lower()


def test_agent_reviews_code(agent):
    out = _turn(
        agent,
        "revisa este código:\n```python\ntry:\n    x = 1\nexcept:\n    pass\n```",
    )
    assert out["reply"]
    assert "except" in out["reply"].lower() or "review" in out["reply"].lower()


def test_agent_fallback_when_no_intent(agent):
    out = _turn(agent, "hola")
    assert "ayudarte" in out["reply"].lower() or "¿qué te gustaría" in out["reply"].lower()
