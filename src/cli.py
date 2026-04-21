"""Interactive CLI chat loop for the Jarvis agent."""

from __future__ import annotations

from dotenv import load_dotenv

from src.agent import build_agent
from src.logging_config import configure_logging, get_logger
from src.memory import Storage


BANNER = r"""
      ___  ________  ________  ___      ___ ___  ________
     |\  \|\   __  \|\   __  \|\  \    /  /|\  \|\   ____\
     \ \  \ \  \|\  \ \  \|\  \ \  \  /  / | \  \ \  \___|_
   __ \ \  \ \   __  \ \   _  _\ \  \/  / / \ \  \ \_____  \
  |\  \\_\  \ \  \ \  \ \  \\  \\ \    / /   \ \  \|____|\  \
  \ \________\ \__\ \__\ \__\\ _\\ \__/ /     \ \__\____\_\  \
   \|________|\|__|\|__|\|__|\|__|\|__|/       \|__|\_________\
                                                   \|_________|
"""


HELP_TEXT = (
    "\nComandos:\n"
    "  /help     — muestra esta ayuda\n"
    "  /history  — últimas entradas de conversación persistidas\n"
    "  /exit     — salir\n"
    "\nCapacidades: agenda (crear evento, listar, hueco libre), "
    "notas y recordatorios, revisión y generación de código.\n"
)


def run_cli() -> None:
    load_dotenv()
    configure_logging()
    log = get_logger("cli")
    storage = Storage()
    agent = build_agent(storage=storage)

    print(BANNER)
    print("Hello, I'm Jarvis. Type /help for commands, /exit to quit.\n")

    conversation: list[dict] = []
    while True:
        try:
            user_input = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            return

        if not user_input:
            continue
        if user_input in {"/exit", "/quit"}:
            print("bye.")
            return
        if user_input == "/help":
            print(HELP_TEXT)
            continue
        if user_input == "/history":
            rows = storage.recent_conversation(limit=10)
            for r in rows:
                print(f"  [{r['created_at']}] {r['role']}: {r['content']}")
            continue

        storage.log_message("user", user_input)
        conversation.append({"role": "user", "content": user_input})

        result = agent.invoke({
            "messages": conversation,
            "iterations": 0,
        })
        reply = result.get("last_response", "")
        conversation = result.get("messages", conversation)

        if reply:
            storage.log_message("assistant", reply)
            print(f"jarvis > {reply}\n")
            log.debug("turn complete in %d iterations", result.get("iterations", 0))


if __name__ == "__main__":
    run_cli()
