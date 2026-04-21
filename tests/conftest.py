"""Shared fixtures: ephemeral storage, built agent."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agent import build_agent
from src.memory import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    return Storage(db_path=tmp_path / "test.db")


@pytest.fixture
def agent(storage: Storage):
    return build_agent(storage=storage)
