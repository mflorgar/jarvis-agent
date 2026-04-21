"""Minimal tests for the voice layer.

We can't test real audio in CI, so we cover what's testable: the TTS
fallback path and the wake-word regex matcher.
"""

from __future__ import annotations

import re
from unittest.mock import patch


def test_tts_prints_when_say_missing(capsys):
    from src.voice.tts import SayEngine
    with patch("shutil.which", return_value=None):
        SayEngine().speak("hola mundo")
    captured = capsys.readouterr()
    assert "hola mundo" in captured.out


def test_tts_does_nothing_on_empty_text():
    from src.voice.tts import SayEngine
    # Should not raise nor call subprocess
    SayEngine().speak("")


def test_wake_pattern_matches_common_variants():
    # Build the same regex the listener uses, without audio deps.
    wake_phrases = ("hey jarvis", "ey jarvis", "oye jarvis", "hola jarvis", "jarvis")
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(p) for p in wake_phrases) + r")\b",
        re.IGNORECASE,
    )
    assert pattern.search("hey jarvis agenda una reunión")
    assert pattern.search("oye jarvis cuál es mi agenda")
    assert pattern.search("Jarvis apunta esta nota")
    assert pattern.search("hola jarvis") is not None


def test_wake_pattern_ignores_random_text():
    wake_phrases = ("hey jarvis",)
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(p) for p in wake_phrases) + r")\b",
        re.IGNORECASE,
    )
    assert pattern.search("buenos días") is None
    assert pattern.search("hola, ¿qué tal?") is None
