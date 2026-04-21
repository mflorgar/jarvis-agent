# Jarvis — personal AI agent

![CI](https://github.com/mflorgar/jarvis-agent/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A personal assistant in your terminal. Built with **LangGraph** and a
classic tool-calling loop. Manages your agenda, notes and reminders,
and helps with code. Persists everything in SQLite.

Runs out of the box with a **mock LLM that still emits real tool
calls** — zero API keys required to demo. Swap to Anthropic or OpenAI
with a single env var.

## Why this repo

A compact reference implementation of an agent with:

- LangGraph state machine (agent ↔ tool loop)
- LangChain `StructuredTool` skills
- Typed state and pydantic-flavoured tool schemas
- Persistent memory (notes, reminders, events, conversation log)
- Interactive CLI + scripted demo runner
- Deterministic tests and GitHub Actions CI

## Stack

- [LangGraph](https://langchain-ai.github.io/langgraph/) for the agent loop
- [LangChain](https://python.langchain.com/) `StructuredTool` for skill schemas
- SQLite (stdlib) for persistent memory
- Python 3.10+, Pytest, GitHub Actions CI

## Architecture

```
     user → agent ───(wants tool?)──▶ tool ──▶ agent → … → END
              ▲                                   │
              └───────── tool result ─────────────┘
```

Full design notes in [`docs/architecture.md`](docs/architecture.md).

## Skills

| Category   | Tools                                                          |
|------------|----------------------------------------------------------------|
| Calendar   | `create_event` · `list_agenda` · `find_free_slot`              |
| Notes      | `create_note` · `list_notes` · `search_notes`                  |
| Reminders  | `create_reminder` · `list_reminders`                           |
| Code       | `explain_code` · `review_code` · `generate_code_snippet`       |

## Quick start

```bash
git clone https://github.com/mflorgar/jarvis-agent.git
cd jarvis-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.cli      # interactive chat
```

Or run the scripted demo:

```bash
python -m src.main
```

### Sample session

```
you   : Agenda una reunión con María mañana a las 10h
jarvis: Listo. Event #1 'María' created 2026-04-22T10:00 → 2026-04-22T11:00.

you   : Muéstrame mi agenda
jarvis: Listo. #1 2026-04-22T10:00 — María

you   : Apunta: comprar regalo de cumpleaños del equipo
jarvis: Listo. Note #1 created with tag 'none'.

you   : Mis notas
jarvis: Listo. #1 [none] comprar regalo de cumpleaños del equipo

you   : Recuérdame enviar el informe mañana a las 9h
jarvis: Listo. Reminder #1 set for 2026-04-22T09:00.

you   : Revisa este código:
        ```python
        print('hola')
        except:
            pass
        ```
jarvis: Listo. Review findings:
        - Uses print() for output; consider `logging` in production code.
        - Bare `except:` catches everything; prefer specific exceptions.
```

Full captured session in [`examples/session_demo.txt`](examples/session_demo.txt).

## Voice mode (optional, macOS)

Jarvis can listen for the wake word "hey jarvis" and talk back using
local speech-to-text (faster-whisper) and macOS' built-in `say`. No API
keys needed.

Install the optional audio dependencies:

```bash
pip install -r requirements-voice.txt
```

First run will download the Whisper model (~150 MB for "base").
Override with `WHISPER_MODEL=tiny` for faster (lower accuracy) or
`WHISPER_MODEL=small` for slower (higher accuracy).

Start voice mode:

```bash
python -m src.voice
```

Say things like:

- *"Hey Jarvis, agenda una reunión con Ana mañana a las 10h"*
- *"Oye Jarvis, muéstrame mi agenda"*
- *"Jarvis, apunta: comprar regalo para el equipo"*

Ctrl+C to stop.

**Wake word accuracy note.** The detector is a Whisper-in-a-loop
approach, dependency-free but with ~1-2 s latency and some false
positives in noisy environments. For production, swap it for
[Picovoice Porcupine](https://picovoice.ai/platform/porcupine/).

## Tests

```bash
pytest
```

17 tests covering: storage (notes, reminders, events, free-slot
finder), skills (event/review/explain/generate), agent end-to-end
with multi-turn conversations, and the voice layer (TTS fallback,
wake-word regex).

## Plugging in real LLM providers

Set the following in your `.env`:

```env
LLM_PROVIDER=anthropic          # or openai
ANTHROPIC_API_KEY=sk-ant-...
```

Uncomment the optional dependencies in `requirements.txt` and add a
backend class in `src/llm.py`. The agent graph does not change.

## Project layout

```
jarvis-agent/
├── src/
│   ├── agent/           # LangGraph state machine
│   ├── skills/          # LangChain StructuredTool skills
│   │   ├── calendar_skills.py
│   │   ├── notes_skills.py
│   │   └── code_skills.py
│   ├── memory/
│   │   └── storage.py   # SQLite wrapper
│   ├── voice/           # Optional: Whisper + say + wake word
│   │   ├── recorder.py
│   │   ├── stt.py
│   │   ├── tts.py
│   │   ├── wake_word.py
│   │   └── voice_cli.py
│   ├── llm.py           # Mock LLM + real adapters
│   ├── cli.py           # Interactive chat loop
│   ├── main.py          # Scripted demo
│   └── logging_config.py
├── tests/               # 17 tests
├── docs/architecture.md
├── examples/
│   └── session_demo.txt
├── .github/workflows/ci.yml
├── .env.example
├── requirements.txt
├── requirements-voice.txt
└── README.md
```

## Roadmap

- [x] Voice in + TTS out (local Whisper + macOS `say`)
- [ ] Swap wake-word detector for Picovoice Porcupine
- [ ] REST API (FastAPI) for programmatic access
- [ ] Web UI (Streamlit / Next.js)
- [ ] Vector memory for long-term context (semantic search)
- [ ] Real LLM backends: Anthropic, OpenAI, local via Ollama
- [ ] More skills: email triage, web search, weather

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Maria Flores](https://github.com/mflorgar).
