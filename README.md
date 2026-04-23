# Jarvis — personal AI agent

![CI](https://github.com/mflorgar/jarvis-agent/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A personal assistant in your terminal. Built with **LangGraph** and a
classic tool-calling loop. Manages your agenda, notes and reminders,
helps with code, opens Mac apps, searches in Chrome and schedules
events in Apple Calendar. Optional voice mode with local Whisper +
macOS `say`. Persists everything in SQLite.

Runs out of the box with a **mock LLM that still emits real tool
calls** — zero API keys required to demo. Swap to Anthropic, OpenAI or
Google Gemini with a single env var.

## Try it online in 1 minute — meet *Eva*

Before you install anything, you can try a lightweight web demo of
this assistant. Her name is **Eva** — the public-facing, browser-only
version of this project. Same personality, no tools, no install.

- **Live demo**: http://eva-demo-sable.vercel.app/
- **Demo repo**: https://github.com/mflorgar/eva-demo

Eva is what you show people when you don't want to walk them through a
terminal install. Jarvis (this repo) is the full thing: voice, tool
calling, Mac integration, CI, tests, local memory. Eva is the teaser.

---

## Can I try the full Jarvis myself?

Yes. Here is the shortest possible path on macOS:

```bash
git clone https://github.com/mflorgar/jarvis-agent.git
cd jarvis-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.cli       # text chat with the MOCK LLM (no API keys)
```

That already works: you can create events, notes, reminders, ask for
code review — all with a local rule-based LLM that emits real tool
calls. No network involved.

Want real LLM answers? Add your own API key:

```bash
pip install -r requirements-gemini.txt
cat > .env <<'EOF'
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
EOF
python -m src.cli
```

Want voice?

```bash
brew install portaudio
pip install -r requirements-voice.txt
python -m src.voice
```

Say *"hola"* to activate, then just talk. Say *"adiós"* to exit.

Full details below.

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

| Category   | Tools                                                                      |
|------------|----------------------------------------------------------------------------|
| Calendar   | `create_event` · `list_agenda` · `find_free_slot`                          |
| Notes      | `create_note` · `list_notes` · `search_notes`                              |
| Reminders  | `create_reminder` · `list_reminders`                                       |
| Code       | `explain_code` · `review_code` · `generate_code_snippet`                   |
| Browser    | `open_url` · `new_tab_chrome` · `close_tab_chrome` · `search_google`       |
| Apps (Mac) | `open_app` (Calculator, Spotify, Notes, Finder…)                           |
| Calendar.app | `schedule_calendar_event` (macOS Calendar via AppleScript)               |

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

### Browser + apps del Mac (con Gemini)

Con `LLM_PROVIDER=gemini` configurado, Jarvis entiende órdenes en lenguaje natural:

```
you   : abre YouTube en Chrome
jarvis: Listo. Abierto https://www.youtube.com en el navegador.

you   : busca en google "ingeniera ai automation paris"
jarvis: Listo. Abierto https://www.google.com/search?q=... en el navegador.

you   : abre la calculadora
jarvis: Listo. App 'Calculator' abierta.

you   : agéndame una reunión mañana a las 10am con mi calendar
jarvis: Listo. Evento 'Nuevo evento' creado en Calendar 2026-04-22T10:00 → 2026-04-22T11:00.
```

Los comandos Mac usan `open` y `osascript` (AppleScript), así que funcionan sin dependencias adicionales en macOS.

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

Tests cubren: storage (notes, reminders, events, free-slot finder),
skills (event/review/explain/generate), agente end-to-end con
conversaciones multi-turn, capa de voz (TTS fallback, wake-word
regex), skills de browser/apps (subprocess mockeado) y backend
Gemini (ChatGoogleGenerativeAI mockeado, sin red).

## Plugging in real LLM providers

### Google Gemini (recomendado, tiene plan gratuito)

```bash
pip install -r requirements-gemini.txt
```

En tu `.env` local (nunca lo commitees):

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=tu_key_de_aistudio
GEMINI_MODEL=gemini-2.0-flash
```

Obtén la key gratis en [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
El backend usa `langchain-google-genai` con `bind_tools`, por lo que Gemini emite llamadas a herramientas nativas (no regex). El grafo del agente no cambia.

### Otros proveedores

Anthropic y OpenAI siguen el mismo patrón: instala la dependencia opcional, añade la key al `.env` y ajusta `LLM_PROVIDER`. Las clases backend comparten la firma `invoke(messages, tools) → AIResponse`.

### Seguridad

Las API keys se leen con `os.getenv`. Nunca van al código ni al repo. `.env` está en `.gitignore`. Si una key se te escapa (se pega en un log, chat, repo público…), revócala y genera otra.

## Project layout

```
jarvis-agent/
├── src/
│   ├── agent/           # LangGraph state machine
│   ├── skills/          # LangChain StructuredTool skills
│   │   ├── calendar_skills.py
│   │   ├── notes_skills.py
│   │   ├── code_skills.py
│   │   └── browser_skills.py
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
├── requirements-gemini.txt
└── README.md
```

## Roadmap

- [x] Voice in + TTS out (local Whisper + macOS `say`)
- [x] Gemini backend with native tool calling
- [x] Browser + Mac app skills (Chrome, Calculator, Spotify, Notes, Finder)
- [x] macOS Calendar.app integration via AppleScript
- [ ] Swap wake-word detector for Picovoice Porcupine
- [ ] REST API (FastAPI) for programmatic access
- [ ] Web UI (Streamlit / Next.js)
- [ ] Vector memory for long-term context (semantic search)
- [ ] More real LLM backends: Anthropic, OpenAI, local via Ollama
- [ ] More skills: email triage, web search, weather

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Maria Flores](https://github.com/mflorgar).
