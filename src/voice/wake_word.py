"""Wake-word loop on top of Whisper.

Simple approach, no external wake-word engine needed:
    1. Record a short chunk (2 s) from the mic.
    2. If the RMS level is too low, skip transcription (silent chunk).
    3. Otherwise transcribe with Whisper.
    4. If the transcription contains any wake phrase, yield the chunk
       after the wake word as the "command".
    5. If the chunk didn't contain a full command, record another
       longer chunk for the command body.

For production, swap for Picovoice Porcupine. Kept dependency-free on
purpose to match the rest of the repo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator

from src.logging_config import get_logger

from .recorder import AudioRecorder
from .stt import WhisperTranscriber

logger = get_logger("voice.wake_word")


@dataclass
class WakeWordListener:
    transcriber: WhisperTranscriber
    recorder: AudioRecorder
    wake_phrases: tuple[str, ...] = (
        "hey jarvis", "ey jarvis", "oye jarvis", "hola jarvis", "jarvis",
    )
    listen_chunk_seconds: float = 3.0
    command_chunk_seconds: float = 6.0
    silence_threshold: float = 0.01

    _wake_pattern: re.Pattern = field(init=False)

    def __post_init__(self) -> None:
        phrases = "|".join(re.escape(p) for p in self.wake_phrases)
        self._wake_pattern = re.compile(rf"\b({phrases})\b", re.IGNORECASE)

    def listen(self) -> Iterator[str]:
        """Yield transcribed commands every time the wake word is heard."""
        logger.info("listening for wake word… (Ctrl+C to stop)")
        while True:
            chunk = self.recorder.record(self.listen_chunk_seconds)
            if self.recorder.rms(chunk) < self.silence_threshold:
                continue

            text = self.transcriber.transcribe(chunk).lower()
            if not text:
                continue

            logger.debug("heard: %r", text)
            match = self._wake_pattern.search(text)
            if not match:
                continue

            tail = text[match.end():].strip(" ,.!?")
            if tail:
                # Wake word + command came in the same chunk → good to go.
                logger.info("wake+command in one chunk: %s", tail)
                yield tail
                continue

            logger.info("wake detected → recording command for %.1fs",
                        self.command_chunk_seconds)
            command_chunk = self.recorder.record(self.command_chunk_seconds)
            command = self.transcriber.transcribe(command_chunk).strip()
            if command:
                yield command
