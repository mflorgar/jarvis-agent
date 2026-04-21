"""Thin sounddevice wrapper to capture microphone audio as numpy arrays."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import numpy as np
    import sounddevice as sd
except ImportError as exc:  # pragma: no cover - optional dep
    raise RuntimeError(
        "Audio dependencies missing. Install with: "
        "pip install 'faster-whisper' sounddevice numpy"
    ) from exc


@dataclass
class AudioRecorder:
    """Record a fixed-duration chunk of audio from the default mic."""

    sample_rate: int = 16000  # Whisper expects 16 kHz mono

    def record(self, seconds: float) -> "np.ndarray":
        frames = int(seconds * self.sample_rate)
        audio = sd.rec(
            frames=frames,
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocking=True,
        )
        return audio.flatten()

    def rms(self, audio: "np.ndarray") -> float:
        """Return the RMS level of a waveform — used to skip silent chunks."""
        if audio.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio**2)))
