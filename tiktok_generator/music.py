"""Schritt 5: Hintergrundmusik auswählen.

Lege einfach lizenzfreie MP3-Dateien in den Ordner assets/music.
(Quellen z.B.: YouTube Audio Library, Pixabay Music, TikTok-eigene Sounds beim Hochladen.)
"""

import random
from pathlib import Path

from moviepy import AudioFileClip, afx

from .config import Config

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}


def pick_music(cfg: Config) -> Path | None:
    tracks = [p for p in cfg.music_dir.glob("*") if p.suffix.lower() in AUDIO_EXTENSIONS]
    return random.choice(tracks) if tracks else None


def music_clip(path: Path, duration: float, cfg: Config) -> AudioFileClip:
    """Lädt die Musik, wiederholt sie bei Bedarf, macht sie leise und blendet aus."""
    clip = AudioFileClip(str(path))
    if clip.duration < duration:
        clip = clip.with_effects([afx.AudioLoop(duration=duration)])
    clip = clip.subclipped(0, duration)
    return clip.with_effects([
        afx.MultiplyVolume(cfg.music_volume),
        afx.AudioFadeIn(1.0),
        afx.AudioFadeOut(2.0),
    ])
