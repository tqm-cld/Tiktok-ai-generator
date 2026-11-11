"""Schritt 2: Den Text mit einer KI-Stimme vorlesen lassen (Microsoft Edge TTS, kostenlos).

Wir merken uns dabei, WANN jedes Wort gesprochen wird.
Das brauchen wir später für die animierten Untertitel.
"""

import asyncio
import hashlib
import json
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg  # liefert FFmpeg mit, keine extra Installation nötig

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
    silent: bool = False  # True = Ersatz ohne Ton (Stimme nicht erreichbar)


async def _speak(text: str, voice: str, rate: str, out_path: Path, pitch: str = "+0Hz") -> list[Word]:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary",
                                       connect_timeout=10, receive_timeout=45)
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
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         "anullsrc=r=24000:cl=mono", "-t", f"{duration:.2f}", str(out_path)],
        check=True,
    )
    words = [Word(t, i * per_word, (i + 1) * per_word) for i, t in enumerate(tokens)]
    return VoiceClip(out_path, duration, words, silent=True)


FALLBACK_VOICE = "de-DE-ConradNeural"
_offline = threading.local()   # merkt sich pro Auftrag, ob der Sprachdienst nicht erreichbar ist


def reset_tts_state():
    """Vor jedem neuen Video aufrufen: Sprachdienst wieder versuchen."""
    _offline.down = False


def _is_network_error(e: Exception) -> bool:
    name = type(e).__name__
    return any(k in name for k in ("Connector", "Connection", "DNS", "Timeout", "ClientOSError")) or \
        isinstance(e, (OSError, asyncio.TimeoutError))


def synthesize(text: str, out_path: Path, cfg: Config, rate: str | None = None, voice: str | None = None,
               pitch: str | None = None) -> VoiceClip:
    """Erzeugt eine MP3 mit gesprochenem Text und den Wort-Zeitstempeln.

    rate/pitch: Sprechtempo/Tonhöhe, z. B. "-6%" / "-3Hz"; voice: andere Stimme (z. B. für eine Figur).
    Gleiche Texte werden zwischengespeichert (kein erneuter Abruf beim Neu-Rendern)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rate, pitch, voice = rate or cfg.voice_rate, pitch or "+0Hz", voice or cfg.voice
    key = hashlib.sha256(f"{text}|{voice}|{rate}|{pitch}".encode()).hexdigest()[:24]
    cache_mp3 = cfg.cache_dir / "tts" / f"{key}.mp3"
    cache_json = cache_mp3.with_suffix(".json")
    if cache_mp3.exists() and cache_json.exists():
        shutil.copyfile(cache_mp3, out_path)
        data = json.loads(cache_json.read_text(encoding="utf-8"))
        return VoiceClip(out_path, data["duration"], [Word(**w) for w in data["words"]])

    words, last_error = None, None
    if not getattr(_offline, "down", False):
        for v in dict.fromkeys([voice, FALLBACK_VOICE]):  # erst Wunschstimme, dann Ersatz
            try:
                words = asyncio.run(_speak(text, v, rate, out_path, pitch))
                break
            except Exception as e:  # z. B. keine Internetverbindung oder Stimme nicht verfügbar
                last_error = e
                if _is_network_error(e):
                    _offline.down = True      # nicht bei jeder Szene erneut warten
                    break
    if words is None:
        if last_error is not None:
            print(f"  ⚠ Sprachausgabe nicht erreichbar ({type(last_error).__name__}) → stummer Testmodus.")
        return _silent_fallback(text, out_path)

    duration = audio_duration(out_path)
    if not words:  # Sicherheitsnetz: Wörter gleichmäßig verteilen
        tokens = text.split()
        step = duration / max(1, len(tokens))
        words = [Word(t, i * step, (i + 1) * step) for i, t in enumerate(tokens)]
    cache_mp3.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out_path, cache_mp3)
    cache_json.write_text(json.dumps({"duration": duration, "words": [w.__dict__ for w in words]}), encoding="utf-8")
    return VoiceClip(out_path, duration, words)
