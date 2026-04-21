# Architecture

## Overview

Jarvis is a personal AI assistant built on a classic **LangGraph
tool-calling loop**. It receives a natural-language message, decides
(via the LLM) whether to call a tool, runs the tool, feeds the result
back to the LLM, and loops until the agent produces a final reply.

Everything runs out of the box: the LLM is a keyword-based mock that
still emits real tool calls, so tests and demos never need an API key.
Swap to Anthropic or OpenAI by setting one env var.

## Agent loop

```
   ┌────────────────────────────────┐
   │ user message                   │
   └──────────────┬─────────────────┘
                  ▼
           ┌───────────┐
           │  agent    │◀─────────┐
           └─────┬─────┘          │
       wants tool? yes            │ tool result
                  ▼               │ appended to
             ┌────────┐           │ messages
             │  tool  │───────────┘
             └────────┘
                  │
       wants tool? no
                  ▼
              ┌────┐
              │END │
              └────┘
```

- **agent node**: the LLM (mock or real) inspects the conversation and
  either emits a `ToolCall` or a final message. A hard cap of
  `MAX_ITERATIONS` (5) prevents loops.
- **tool node**: executes the requested tool with the provided args
  and appends a `role=tool` message back to the conversation.

## Layers

```
┌────────────────────────────────────────────────────────┐
│  CLI / Demo                                            │
│    src/cli.py  (interactive chat)                      │
│    src/main.py (scripted demo session)                 │
└──────────────────────┬─────────────────────────────────┘
                       │ drives
                       ▼
┌────────────────────────────────────────────────────────┐
│  Agent (LangGraph)                                     │
│    src/agent/graph.py   — StateGraph wiring            │
│    src/agent/state.py   — typed state                  │
└──────────────────────┬─────────────────────────────────┘
                       │ calls
                       ▼
┌────────────────────────────────────────────────────────┐
│  LLM & Skills                                          │
│    src/llm.py           — MockLLM + real adapters      │
│    src/skills/          — LangChain StructuredTools    │
│      calendar_skills.py · notes_skills.py · code_skills│
└──────────────────────┬─────────────────────────────────┘
                       │ reads / writes
                       ▼
┌────────────────────────────────────────────────────────┐
│  Memory (SQLite)                                       │
│    src/memory/storage.py                               │
│      notes · reminders · events · conversation         │
└────────────────────────────────────────────────────────┘
```

## Skills catalogue

| Category  | Tool                    | Purpose                                   |
|-----------|-------------------------|-------------------------------------------|
| Calendar  | `create_event`          | Create a calendar event                   |
| Calendar  | `list_agenda`           | List upcoming events                      |
| Calendar  | `find_free_slot`        | Find the first free slot of N minutes     |
| Notes     | `create_note`           | Persist a free-text note                  |
| Notes     | `list_notes`            | List recent notes, optionally by tag      |
| Notes     | `search_notes`          | Substring search over notes               |
| Reminders | `create_reminder`       | Create a reminder with a due date         |
| Reminders | `list_reminders`        | List pending reminders                    |
| Code      | `explain_code`          | Parse a Python snippet and summarize it   |
| Code      | `review_code`           | Lightweight heuristic code review         |
| Code      | `generate_code_snippet` | Template-based snippet generation         |

## Why a mock LLM that still emits tool calls

Most "agent demo" repos need an API key to do anything. That creates
friction for reviewers and makes CI fragile. The mock in `llm.py`
inspects the user's message, detects intent from keywords, and returns
a `ToolCall` object with the right arguments — exactly what a real LLM
would return via structured output. The agent graph cannot tell the
difference. Real providers plug in by implementing the same
`invoke(messages, tools) → AIResponse` contract.

## Extending Jarvis

- **Add a new skill**: write a function, wrap it with
  `StructuredTool.from_function`, register it in `src/skills/__init__.py`.
- **Swap the LLM backend**: implement a class with `invoke(messages, tools)`
  that returns an `AIResponse`. Register it in `LLMClient._build_backend`.
- **Add voice**: drop a speech-to-text layer before `cli.py` and a
  text-to-speech layer after. The agent doesn't care where the text
  comes from.
- **Add a REST API**: wrap `agent.invoke(...)` in a FastAPI endpoint
  (the other repos in this portfolio follow that pattern).
