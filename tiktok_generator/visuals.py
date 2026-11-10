"""Schritt 3: Bildmaterial für jeden Shot besorgen – Stockvideos und (im Hybrid-Modus) KI-Szenen.

Modi:
  - "stock":   alle Shots aus kostenlosen Pexels-Stockvideos
  - "preview": Hybrid-Vorschau – die geplanten KI-Momente werden im Video markiert,
               es wird aber noch nichts bezahlt (Stockvideo als Platzhalter)
  - "<modell>": Hybrid – KI-Momente vom gewählten KI-Videomodell, Rest Stockvideos.
               Ein Modell ist erst nutzbar, wenn es in AI_PROVIDERS eingetragen ist –
               das passiert ERST nach deiner ausdrücklichen Zustimmung.

Einmal erzeugte KI-Clips werden zwischengespeichert. Wird dasselbe Video erneut gerendert,
wird nicht noch einmal bezahlt.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .config import Config
from .costs import model_by_key
from .media import fetch_media
from .story import Scene

FREE_MODES = {"stock", "preview"}


class ProviderNotEnabled(RuntimeError):
    pass


@dataclass
class ShotMedia:
    primary: Path                    # Material für den Anfang des Shots (bei KI-Momenten: der KI-Clip)
    secondary: Optional[Path] = None  # Material für weitere Schnitte innerhalb desselben Shots
    ai: bool = False                 # echte KI-Szene
    planned_ai: bool = False         # in der Vorschau als KI-Moment markiert


# Signatur eines KI-Videoanbieters: (prompt, sekunden, zieldatei, cfg) -> Pfad zum MP4
AIGenerator = Callable[[str, float, Path, Config], Path]

# Hier werden freigegebene KI-Videomodelle eingetragen. Aktuell: keines (wartet auf Zustimmung).
AI_PROVIDERS: dict[str, AIGenerator] = {}


def available_modes() -> set[str]:
    return FREE_MODES | set(AI_PROVIDERS)


def _cached_ai_clip(model: str, prompt: str, seconds: float, cfg: Config) -> Path:
    key = hashlib.sha256(f"{model}|{seconds}|{prompt}".encode()).hexdigest()[:20]
    target = cfg.cache_dir / "ai_clips" / f"{model}_{key}.mp4"
    if target.exists() and target.stat().st_size > 0:
        return target                         # schon bezahlt → wiederverwenden
    target.parent.mkdir(parents=True, exist_ok=True)
    return AI_PROVIDERS[model](prompt, seconds, target, cfg)


def get_shot_media(scene: Scene, cfg: Config, target_dir: Path, mode: str = "stock",
                   is_ai_moment: bool = False, ai_seconds: float = 4) -> ShotMedia:
    stock = fetch_media(scene.visual_query, cfg, target_dir)
    if not is_ai_moment or mode == "stock":
        return ShotMedia(stock)
    if mode == "preview":
        return ShotMedia(stock, planned_ai=True)
    if mode not in AI_PROVIDERS:
        try:
            name = model_by_key(mode).name
        except KeyError:
            name = mode
        raise ProviderNotEnabled(
            f"❌ {name} ist noch nicht freigeschaltet. KI-Videomodelle werden erst nach deiner Zustimmung "
            "eingebaut – bitte „Hybrid-Vorschau“ oder „Nur Stockvideos“ verwenden."
        )
    clip = _cached_ai_clip(mode, scene.visual_prompt, ai_seconds, cfg)
    return ShotMedia(clip, secondary=stock, ai=True)
