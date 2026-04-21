"""LangGraph wiring for the Jarvis agent.

Classic tool-calling loop:
    agent → (tool? yes) → tool → agent → … → END
                    │
                    └─→ (no) → END
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.llm import LLMClient
from src.logging_config import get_logger
from src.memory import Storage
from src.skills import build_all_tools

from .state import AgentState

logger = get_logger("agent.graph")

MAX_ITERATIONS = 5


def build_agent(
    storage: Storage | None = None,
    llm: LLMClient | None = None,
):
    """Compile the agent graph with the given storage and LLM backends."""
    storage = storage or Storage()
    llm = llm or LLMClient()
    tools = build_all_tools(storage)
    tools_by_name = {t.name: t for t in tools}

    def agent_node(state: AgentState) -> AgentState:
        iterations = state.get("iterations", 0) + 1
        if iterations > MAX_ITERATIONS:
            logger.warning("agent: max iterations reached (%d)", MAX_ITERATIONS)
            return {
                **state,
                "last_response": "Se alcanzó el máximo de iteraciones sin concluir.",
                "pending_tool": None,
                "iterations": iterations,
            }

        response = llm.invoke(state["messages"], tools)
        if response.wants_tool:
            call = response.tool_calls[0]
            logger.info("agent: requesting tool '%s' with %s", call.name, call.args)
            return {
                **state,
                "pending_tool": {"name": call.name, "args": call.args, "id": call.id},
                "iterations": iterations,
            }

        logger.info("agent: final reply (iter=%d)", iterations)
        messages = [*state["messages"], {"role": "assistant", "content": response.content}]
        return {
            **state,
            "messages": messages,
            "last_response": response.content,
            "pending_tool": None,
            "iterations": iterations,
        }

    def tool_node(state: AgentState) -> AgentState:
        pending = state["pending_tool"]
        tool = tools_by_name.get(pending["name"])
        if tool is None:
            output = f"Unknown tool '{pending['name']}'."
            logger.warning("tool: %s", output)
        else:
            try:
                output = tool.invoke(pending["args"])
            except Exception as exc:  # noqa: BLE001
                output = f"Tool '{pending['name']}' failed: {exc}"
                logger.exception("tool: %s", output)
        logger.info("tool: '%s' → %s", pending["name"], output[:120])
        messages = [
            *state["messages"],
            {"role": "tool", "tool_name": pending["name"], "content": str(output)},
        ]
        return {**state, "messages": messages, "pending_tool": None}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tool", tool_node)

    graph.set_entry_point("agent")

    def _route(state: AgentState) -> str:
        return "tool" if state.get("pending_tool") else END

    graph.add_conditional_edges("agent", _route, {"tool": "tool", END: END})
    graph.add_edge("tool", "agent")

    return graph.compile()
