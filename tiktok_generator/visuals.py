"""Schritt 3: Bildmaterial für jeden Shot besorgen – über einen austauschbaren "Anbieter".

Aktuell freigeschaltet:
  - "stock": kostenlose Hochkant-Stockvideos von Pexels (Ersatz: generierte Hintergründe)

Kostenpflichtige KI-Videomodelle (Veo, Kling, Hailuo, ...) sind in costs.py mit Preisen
aufgelistet, werden aber ERST nach deiner ausdrücklichen Freigabe angebunden.
Neue Anbieter bekommen hier eine eigene Funktion und einen Eintrag in PROVIDERS.
"""

from pathlib import Path

from .config import Config
from .costs import model_by_key
from .media import fetch_media
from .story import Scene


class ProviderNotEnabled(RuntimeError):
    pass


def _stock(scene: Scene, cfg: Config, target_dir: Path) -> Path:
    return fetch_media(scene.visual_query, cfg, target_dir)


PROVIDERS = {
    "stock": _stock,
}


def get_media(scene: Scene, cfg: Config, target_dir: Path, provider: str = "stock") -> Path:
    if provider not in PROVIDERS:
        name = model_by_key(provider).name if provider else provider
        raise ProviderNotEnabled(
            f"❌ {name} ist noch nicht freigeschaltet. Kostenpflichtige Videomodelle werden erst nach deiner "
            "Zustimmung eingebaut – bitte den Testmodus verwenden."
        )
    return PROVIDERS[provider](scene, cfg, target_dir)


def available_providers() -> set[str]:
    return set(PROVIDERS)
