"""Zentrale Einstellungen. Alles, was man anpassen möchte, steht hier."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Liest die Datei ".env" (falls vorhanden) und legt die Werte als Umgebungsvariablen ab.
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    # --- Video ---
    width: int = 1080          # 9:16-Format
    height: int = 1920
    fps: int = 30
    min_seconds: int = 30
    max_seconds: int = 60

    # --- API-Schlüssel (leer = Demo-Modus) ---
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    pexels_api_key: str = field(default_factory=lambda: os.getenv("PEXELS_API_KEY", ""))

    # --- Geschichte ---
    claude_model: str = "claude-opus-5-5"
    language: str = field(default_factory=lambda: os.getenv("STORY_LANGUAGE", "Deutsch"))

    # --- Stimme ---
    voice: str = field(default_factory=lambda: os.getenv("TTS_VOICE", "de-DE-FlorianMultilingualNeural"))
    voice_rate: str = field(default_factory=lambda: os.getenv("TTS_RATE", "+5%"))

    # --- Musik ---
    music_volume: float = field(default_factory=lambda: float(os.getenv("MUSIC_VOLUME", "0.12")))

    # --- Untertitel ---
    words_per_caption: int = 3
    font_size: int = 95
    caption_y: float = 0.62    # vertikale Position (0 = oben, 1 = unten)

    # --- Ordner ---
    music_dir: Path = PROJECT_ROOT / "assets" / "music"
    fonts_dir: Path = PROJECT_ROOT / "assets" / "fonts"
    output_dir: Path = PROJECT_ROOT / "output"
    cache_dir: Path = PROJECT_ROOT / "cache"

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)
