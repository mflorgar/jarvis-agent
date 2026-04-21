"""Text-to-speech via macOS' built-in `say` command.

Zero dependencies, zero setup. Supports Spanish voices (Mónica, Paulina,
Jorge) and any other installed locale. Falls back gracefully on Linux
or when `say` is missing: it just prints the text.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class SayEngine:
    voice: str = "Mónica"   # Spanish (es_ES). Use "Paulina" for es_MX.
    rate: int = 180         # words per minute

    def speak(self, text: str) -> None:
        if not text:
            return
        say_bin = shutil.which("say")
        if say_bin is None:
            print(f"[TTS fallback] {text}")
            return
        subprocess.run(
            [say_bin, "-v", self.voice, "-r", str(self.rate), text],
            check=False,
        )
