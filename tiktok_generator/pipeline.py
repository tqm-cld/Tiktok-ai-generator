"""Die komplette Videoerstellung in einer Funktion – genutzt von der Weboberfläche und von main.py.

Während der Arbeit wird `progress(prozent, text)` aufgerufen, damit man den Fortschritt anzeigen kann.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from proglog import ProgressBarLogger

from .config import Config
from . import ledger
from .story import Story, demo_story, generate_story, pick_ai_moments
from .video import PAUSE_BETWEEN_SCENES, build_video
from .visuals import get_shot_media
from .voice import synthesize

ProgressFn = Callable[[int, str], None]

# Wie viel Prozent jeder Schritt am Gesamtfortschritt ausmacht
STEP_STORY = (0, 15)
STEP_VOICE = (15, 28)
STEP_MEDIA = (28, 40)
STEP_RENDER = (40, 100)


@dataclass
class VideoResult:
    video_path: Path
    title: str
    caption: str
    duration: float
    demo: bool
    warnings: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0            # tatsächlich angefallene Kosten dieses Videos
    ai_shots: list[int] = field(default_factory=list)  # Nummern der Shots, die (geplante) KI-Szenen sind


def slugify(text: str) -> str:
    text = text.lower()
    for a, b in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:40] or "video"


def _scale(step: tuple[int, int], fraction: float) -> int:
    start, end = step
    return int(start + (end - start) * max(0.0, min(1.0, fraction)))


class _RenderProgress(ProgressBarLogger):
    """Leitet den Fortschritt von MoviePy (Bilder gerendert) an unsere progress-Funktion weiter."""

    def __init__(self, progress: ProgressFn):
        super().__init__()
        self._progress = progress
        self._last = -1

    def bars_callback(self, bar, attr, value, old_value=None):
        if bar != "frame_index" or attr != "index":
            return
        total = self.bars[bar].get("total") or 1
        percent = _scale(STEP_RENDER, value / total)
        if percent != self._last:
            self._last = percent
            self._progress(percent, f"Video wird geschnitten und gerendert … ({int(100 * value / total)} %)")


def make_video(topic: str, cfg: Config, seconds: int | None = None,
               progress: ProgressFn | None = None, demo: bool = False,
               fact_check: bool = True, mode: str = "stock", ai_moments: int = 3) -> VideoResult:
    """mode: "stock" (nur Stockvideos), "preview" (Hybrid-Vorschau, kostenlos) oder ein freigegebenes
    KI-Videomodell (Hybrid). ai_moments: wie viele Shots im Hybrid-Modus KI-Szenen werden (1-4)."""
    report = progress or (lambda p, msg: print(f"[{p:3d}%] {msg}"))

    # ① Recherche + Skript
    use_demo = demo or not cfg.anthropic_api_key
    if use_demo:
        report(_scale(STEP_STORY, 0.2), "Testmodus ohne Claude: geprüftes Demo-Skript wird verwendet …")
        story: Story = demo_story(seconds)
    else:
        report(_scale(STEP_STORY, 0.1), "Recherchiere Fakten im Web und prüfe sie …" if fact_check
               else "Skript wird geschrieben …")
        story = generate_story(topic, cfg, seconds, fact_check=fact_check, ai_moments=ai_moments)
        ledger.record("claude", story.script_cost_usd, f"Skript: {story.title}")
    report(STEP_STORY[1], f"Skript fertig: „{story.title}“ ({len(story.scenes)} Shots, {len(story.sources)} Quellen)")

    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(story.title)}"
    work_dir = cfg.cache_dir / run_id

    # ② Stimme – der Hook wird etwas langsamer und eindringlicher gesprochen
    voices = []
    for i, scene in enumerate(story.scenes):
        report(_scale(STEP_VOICE, i / len(story.scenes)), f"KI-Stimme spricht Shot {i + 1} von {len(story.scenes)} …")
        rate = "-4%" if i == 0 else None
        voices.append(synthesize(scene.text, work_dir / f"voice_{i:02d}.mp3", cfg, rate=rate))

    # ③ Bildmaterial – im Hybrid-Modus bekommen die wichtigsten Momente KI-Szenen
    ai_flags = pick_ai_moments(story.scenes, ai_moments) if mode != "stock" else [False] * len(story.scenes)
    media = []
    for i, (scene, flag) in enumerate(zip(story.scenes, ai_flags)):
        what = "KI-Szene" if flag and mode != "preview" else "Bildmaterial"
        report(_scale(STEP_MEDIA, i / len(story.scenes)), f"{what} für Shot {i + 1}: „{scene.visual_query}“ …")
        media.append(get_shot_media(scene, cfg, work_dir / "media", mode=mode, is_ai_moment=flag))

    # ④–⑥ Schnitt, Untertitel, Soundeffekte, Musik
    report(STEP_RENDER[0], "Schnitt, Untertitel, Soundeffekte und Musik werden eingefügt …")
    out_path = cfg.output_dir / f"{run_id}.mp4"
    build_video(voices, media, out_path, cfg, logger=_RenderProgress(report),
                scenes=story.scenes, hook_title=story.hook_title)

    caption = f"{story.title} " + " ".join(f"#{h.lstrip('#')}" for h in story.hashtags)
    out_path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    out_path.with_suffix(".json").write_text(story.model_dump_json(indent=2), encoding="utf-8")

    duration = sum(v.duration + PAUSE_BETWEEN_SCENES for v in voices)
    warnings = []
    if any(v.silent for v in voices):
        warnings.append("Die KI-Stimme war nicht erreichbar (Internetverbindung?) – das Video hat keine Sprachausgabe.")
    if mode == "preview":
        warnings.append(f"Hybrid-Vorschau: Die {sum(ai_flags)} markierten Shots („KI-SZENE · VORSCHAU“) würden "
                        "später KI-Szenen. Noch wurde nichts bezahlt.")
    if not cfg.pexels_api_key:
        warnings.append("Ohne Pexels-Schlüssel werden generierte Hintergründe statt echter Videoclips verwendet.")
    if use_demo:
        warnings.append("Testmodus ohne Claude: Es wurde das Demo-Skript zur Erdrotation verwendet, nicht dein Thema.")

    report(100, "Fertig!")
    return VideoResult(out_path, story.title, caption, duration, use_demo, warnings,
                       [s.model_dump() for s in story.sources], round(story.script_cost_usd, 4),
                       [i + 1 for i, f in enumerate(ai_flags) if f])
