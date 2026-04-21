"""Voice entry point: wake-word loop + agent + TTS reply."""

from __future__ import annotations

from dotenv import load_dotenv

from src.agent import build_agent
from src.logging_config import configure_logging, get_logger
from src.memory import Storage

from .recorder import AudioRecorder
from .stt import WhisperTranscriber
from .tts import SayEngine
from .wake_word import WakeWordListener


def run_voice() -> None:
    load_dotenv()
    configure_logging()
    log = get_logger("voice.cli")

    storage = Storage()
    agent = build_agent(storage=storage)
    say = SayEngine()
    transcriber = WhisperTranscriber()
    recorder = AudioRecorder()
    listener = WakeWordListener(transcriber=transcriber, recorder=recorder)

    say.speak("Hola, soy Jarvis. Estoy listo para escucharte.")
    log.info("Say 'hey jarvis' followed by a command.")

    conversation: list[dict] = []
    try:
        for user_text in listener.listen():
            log.info("user → %s", user_text)
            storage.log_message("user", user_text)
            conversation.append({"role": "user", "content": user_text})

            result = agent.invoke({"messages": conversation, "iterations": 0})
            reply = result.get("last_response", "")
            conversation = result.get("messages", conversation)

            if reply:
                storage.log_message("assistant", reply)
                log.info("jarvis → %s", reply)
                print(f"jarvis > {reply}")
                say.speak(reply)
    except KeyboardInterrupt:
        print("\nbye.")
        say.speak("Adiós.")


if __name__ == "__main__":
    run_voice()
