"""Structured logging for the Jarvis agent."""

from __future__ import annotations

import logging
import os
import sys


def configure_logging(level: str | None = None) -> None:
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="%(asctime)s %(levelname)-5s %(name)-20s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    for noisy in ("httpx", "urllib3", "anthropic", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
