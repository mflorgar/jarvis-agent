"""Code skills: static analysis and heuristic suggestions.

These tools are deliberately LLM-free so the whole demo runs without
any API key. The agent can still delegate to the LLM for deeper
analysis in its final reply.
"""

from __future__ import annotations

import ast
from typing import List

from langchain_core.tools import StructuredTool


def _count_python_structures(code: str) -> dict[str, int]:
    tree = ast.parse(code)
    return {
        "functions": sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree)),
        "async_functions": sum(isinstance(n, ast.AsyncFunctionDef) for n in ast.walk(tree)),
        "classes": sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
        "imports": sum(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree)),
        "if_statements": sum(isinstance(n, ast.If) for n in ast.walk(tree)),
        "loops": sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree)),
    }


def _explain_code(code: str) -> str:
    try:
        stats = _count_python_structures(code)
    except SyntaxError as exc:
        return f"Python syntax error at line {exc.lineno}: {exc.msg}"
    parts = [
        f"{stats['functions']} function(s)",
        f"{stats['async_functions']} async function(s)",
        f"{stats['classes']} class(es)",
        f"{stats['imports']} import(s)",
        f"{stats['if_statements']} conditional(s)",
        f"{stats['loops']} loop(s)",
    ]
    summary = ", ".join(p for p in parts if not p.startswith("0 "))
    return (
        "Parsed Python code successfully. "
        + (summary if summary else "No top-level structures detected.")
    )


def _review_code(code: str) -> str:
    findings = []
    if "print(" in code and "logging" not in code:
        findings.append("Uses print() for output; consider `logging` in production code.")
    if "except:" in code:
        findings.append("Bare `except:` catches everything; prefer specific exceptions.")
    if "eval(" in code or "exec(" in code:
        findings.append("Uses `eval`/`exec`; security risk with untrusted input.")
    if "TODO" in code or "FIXME" in code:
        findings.append("Unresolved TODO/FIXME markers left in code.")
    if "password" in code.lower() and "=" in code:
        findings.append("Possible hardcoded credential; move to environment variables.")
    if not findings:
        return "No obvious issues detected by the heuristic review."
    return "Review findings:\n- " + "\n- ".join(findings)


def _generate_snippet(description: str, language: str = "python") -> str:
    """Very small template generator to keep the demo LLM-free.
    A real implementation would delegate to the LLM with a constrained prompt.
    """
    language = language.lower()
    if language != "python":
        return f"Snippet generation for '{language}' is not implemented in the mock skill."
    description_lower = description.lower()
    if "fastapi" in description_lower and "endpoint" in description_lower:
        return (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/health')\n"
            "def health() -> dict:\n"
            "    return {'status': 'ok'}\n"
        )
    if "pydantic" in description_lower and "model" in description_lower:
        return (
            "from pydantic import BaseModel, Field\n\n"
            "class Example(BaseModel):\n"
            "    name: str = Field(..., min_length=1)\n"
            "    age: int = Field(..., ge=0)\n"
        )
    if "retry" in description_lower:
        return (
            "import time\n\n"
            "def retry(fn, attempts: int = 3, delay: float = 1.0):\n"
            "    for i in range(attempts):\n"
            "        try:\n"
            "            return fn()\n"
            "        except Exception:\n"
            "            if i == attempts - 1:\n"
            "                raise\n"
            "            time.sleep(delay * 2 ** i)\n"
        )
    return (
        "# Snippet not in the built-in template catalogue.\n"
        "# A real backend would ask the LLM with: "
        f"'{description}'"
    )


def build_code_tools() -> List[StructuredTool]:
    return [
        StructuredTool.from_function(
            func=_explain_code,
            name="explain_code",
            description=(
                "Parse a Python snippet and describe its structure "
                "(functions, classes, imports, loops)."
            ),
        ),
        StructuredTool.from_function(
            func=_review_code,
            name="review_code",
            description=(
                "Run a lightweight heuristic review of a Python snippet. "
                "Detects bare excepts, eval/exec, TODOs and hardcoded credentials."
            ),
        ),
        StructuredTool.from_function(
            func=_generate_snippet,
            name="generate_code_snippet",
            description="Generate a small code snippet from a description.",
        ),
    ]
