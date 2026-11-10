"""Schritt 2: Den Text mit einer KI-Stimme vorlesen lassen (Microsoft Edge TTS, kostenlos).

Wir merken uns dabei, WANN jedes Wort gesprochen wird.
Das brauchen wir später für die animierten Untertitel.
"""

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts

from .config import Config


@dataclass
class Word:
    text: str
    start: float  # Sekunden
    end: float


@dataclass
class VoiceClip:
    path: Path
    duration: float
    words: list[Word]


async def _speak(text: str, voice: str, rate: str, out_path: Path) -> list[Word]:
    communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words: list[Word] = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # edge-tts gibt Zeiten in 100-Nanosekunden-Einheiten an
                start = chunk["offset"] / 10_000_000
                dur = chunk["duration"] / 10_000_000
                words.append(Word(chunk["text"], start, start + dur))
    return words


def audio_duration(path: Path) -> float:
    """Liest die Länge einer Audiodatei mit ffprobe aus."""
    from moviepy import AudioFileClip

    with AudioFileClip(str(path)) as clip:
        return clip.duration


def _silent_fallback(text: str, out_path: Path) -> VoiceClip:
    """Offline-Ersatz: Stille mit geschätzten Wortzeiten (nur zum Testen)."""
    tokens = text.split()
    per_word = 0.38
    duration = max(1.0, len(tokens) * per_word + 0.3)
    out_path = out_path.with_suffix(".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         "anullsrc=r=24000:cl=mono", "-t", f"{duration:.2f}", str(out_path)],
        check=True,
    )
    words = [Word(t, i * per_word, (i + 1) * per_word) for i, t in enumerate(tokens)]
    return VoiceClip(out_path, duration, words)


def synthesize(text: str, out_path: Path, cfg: Config) -> VoiceClip:
    """Erzeugt eine MP3 mit gesprochenem Text und den Wort-Zeitstempeln."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        words = asyncio.run(_speak(text, cfg.voice, cfg.voice_rate, out_path))
    except Exception as e:  # z.B. keine Internetverbindung
        print(f"  ⚠ Sprachausgabe fehlgeschlagen ({type(e).__name__}) → stummer Testmodus.")
        return _silent_fallback(text, out_path)

    duration = audio_duration(out_path)
    if not words:  # Sicherheitsnetz: Wörter gleichmäßig verteilen
        tokens = text.split()
        step = duration / max(1, len(tokens))
        words = [Word(t, i * step, (i + 1) * step) for i, t in enumerate(tokens)]
    return VoiceClip(out_path, duration, words)
