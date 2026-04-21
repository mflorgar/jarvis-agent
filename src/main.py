"""Demo runner that exercises a handful of user turns end-to-end.

Useful as a smoke test and to show an example session in the README.
"""

from __future__ import annotations

from dotenv import load_dotenv

from src.agent import build_agent
from src.logging_config import configure_logging, get_logger
from src.memory import Storage


DEMO_TURNS = [
    "Agenda una reunión con María mañana a las 10h",
    "Muéstrame mi agenda",
    "Apunta: comprar regalo de cumpleaños del equipo",
    "Mis notas",
    "Recuérdame enviar el informe mañana a las 9h",
    "Revisa este código: ```python\nprint('hola')\nexcept:\n    pass\n```",
]


def run_demo() -> None:
    load_dotenv()
    configure_logging()
    log = get_logger("demo")

    # Use an ephemeral DB for the demo so every run starts from scratch
    import tempfile
    from pathlib import Path
    db_path = Path(tempfile.mkdtemp()) / "jarvis_demo.db"
    storage = Storage(db_path=str(db_path))

    agent = build_agent(storage=storage)
    conversation: list[dict] = []

    for user in DEMO_TURNS:
        conversation.append({"role": "user", "content": user})
        result = agent.invoke({"messages": conversation, "iterations": 0})
        conversation = result.get("messages", conversation)
        reply = result.get("last_response", "")
        print(f"you   : {user}")
        print(f"jarvis: {reply}\n")
        log.debug("turn done in %d iterations", result.get("iterations", 0))


if __name__ == "__main__":
    run_demo()
