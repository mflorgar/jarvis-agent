"""Voice interface for Jarvis: wake word + speech-to-text + text-to-speech.

Deliberately kept as an OPTIONAL module. If the audio dependencies
aren't installed, the text-only CLI still works. Import errors are
surfaced with a friendly message when the user tries to use voice.
"""

from __future__ import annotations

__all__ = ["AudioRecorder", "WhisperTranscriber", "SayEngine", "WakeWordListener"]


def __getattr__(name):  # lazy import so optional deps don't break anything else
    if name == "AudioRecorder":
        from .recorder import AudioRecorder
        return AudioRecorder
    if name == "WhisperTranscriber":
        from .stt import WhisperTranscriber
        return WhisperTranscriber
    if name == "SayEngine":
        from .tts import SayEngine
        return SayEngine
    if name == "WakeWordListener":
        from .wake_word import WakeWordListener
        return WakeWordListener
    raise AttributeError(f"module 'src.voice' has no attribute {name!r}")
