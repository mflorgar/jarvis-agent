"""Speech-to-text wrapper around faster-whisper (local, no API)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from faster_whisper import WhisperModel  # type: ignore
except ImportError as exc:  # pragma: no cover - optional dep
    raise RuntimeError(
        "faster-whisper no está instalado. "
        "Instálalo con: pip install faster-whisper"
    ) from exc


@dataclass
class WhisperTranscriber:
    """Lazy-loaded Whisper model.

    Default size is 'base' which is a good trade-off between latency and
    accuracy on a MacBook. Override via env var WHISPER_MODEL or the
    constructor.
    """

    model_size: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "base"))
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "es"

    _model: "WhisperModel | None" = None

    @property
    def model(self) -> "WhisperModel":
        if self._model is None:
            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio) -> str:
        segments, _info = self.model.transcribe(
            audio, language=self.language, beam_size=1
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
