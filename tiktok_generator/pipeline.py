"""Die komplette Videoerstellung in einer Funktion – genutzt von der Weboberfläche und von main.py.

Während der Arbeit wird `progress(prozent, text)` aufgerufen, damit man den Fortschritt anzeigen kann.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from proglog import ProgressBarLogger

from .config import Config
from .media import fetch_media
from .story import Story, demo_story, generate_story
from .video import PAUSE_BETWEEN_SCENES, build_video
from .voice import synthesize

ProgressFn = Callable[[int, str], None]

# Wie viel Prozent jeder Schritt am Gesamtfortschritt ausmacht
STEP_STORY = (0, 10)
STEP_VOICE = (10, 25)
STEP_MEDIA = (25, 40)
STEP_RENDER = (40, 100)


@dataclass
class VideoResult:
    video_path: Path
    title: str
    caption: str
    duration: float
    demo: bool
    warnings: list[str]


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
            self._progress(percent, f"Video wird gerendert … ({int(100 * value / total)} %)")


def make_video(topic: str, cfg: Config, seconds: int | None = None,
               progress: ProgressFn | None = None, demo: bool = False) -> VideoResult:
    report = progress or (lambda p, msg: print(f"[{p:3d}%] {msg}"))

    # ① Geschichte
    use_demo = demo or not cfg.anthropic_api_key
    report(_scale(STEP_STORY, 0.1), "Geschichte wird geschrieben …" if not use_demo
           else "Demo-Modus: Beispielgeschichte wird verwendet …")
    story: Story = demo_story(seconds) if use_demo else generate_story(topic, cfg, seconds)
    report(STEP_STORY[1], f"Geschichte fertig: „{story.title}“ ({len(story.scenes)} Szenen)")

    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(story.title)}"
    work_dir = cfg.cache_dir / run_id

    # ② Stimme
    voices = []
    for i, scene in enumerate(story.scenes):
        report(_scale(STEP_VOICE, i / len(story.scenes)), f"KI-Stimme spricht Szene {i + 1} von {len(story.scenes)} …")
        voices.append(synthesize(scene.text, work_dir / f"voice_{i:02d}.mp3", cfg))

    # ③ Bilder / Videos
    media = []
    for i, scene in enumerate(story.scenes):
        report(_scale(STEP_MEDIA, i / len(story.scenes)), f"Suche Bildmaterial: „{scene.visual_query}“ …")
        media.append(fetch_media(scene.visual_query, cfg, work_dir / "media"))

    # ④–⑥ Untertitel, Musik, Zusammenschnitt
    report(STEP_RENDER[0], "Untertitel und Musik werden eingefügt …")
    out_path = cfg.output_dir / f"{run_id}.mp4"
    build_video(voices, media, out_path, cfg, logger=_RenderProgress(report))

    caption = f"{story.title} " + " ".join(f"#{h.lstrip('#')}" for h in story.hashtags)
    out_path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    out_path.with_suffix(".json").write_text(story.model_dump_json(indent=2), encoding="utf-8")

    duration = sum(v.duration + PAUSE_BETWEEN_SCENES for v in voices)
    warnings = []
    if any(v.silent for v in voices):
        warnings.append("Die KI-Stimme war nicht erreichbar (Internetverbindung?) – das Video hat keine Sprachausgabe.")
    if not cfg.pexels_api_key:
        warnings.append("Ohne Pexels-Schlüssel werden Farbverläufe statt echter Bilder verwendet.")

    report(100, "Fertig!")
    return VideoResult(out_path, story.title, caption, duration, use_demo, warnings)
