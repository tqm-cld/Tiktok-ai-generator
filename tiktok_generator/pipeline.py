"""Die komplette Videoerstellung – genutzt von der Weboberfläche und von main.py.

Zwei Schritte:
  1. plan_story():   Skript erstellen (Claude oder kostenloser Offline-Generator) + Skript-Prüfung
  2. render_story(): Stimmen, Bilder, Schnitt, Ton, Export + Prüfung der fertigen MP4
make_video() führt beide Schritte nacheinander aus.
Während der Arbeit wird `progress(prozent, text)` aufgerufen.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from proglog import ProgressBarLogger

from . import ledger, qc
from .audio import VOICE_STYLES, assign_voices
from .config import Config
from .formats import get_format
from .offline import generate_offline
from .series import load_series, record_episode
from .story import Story, StoryError, generate_format_story, generate_story, pick_ai_moments
from .video import build_video
from .visuals import get_shot_media
from .voice import reset_tts_state, synthesize

ProgressFn = Callable[[int, str], None]

STEP_STORY = (0, 12)
STEP_VOICE = (12, 26)
STEP_MEDIA = (26, 36)
STEP_RENDER = (36, 95)
STEP_QC = (95, 100)


@dataclass
class VideoResult:
    video_path: Path
    title: str
    caption: str
    duration: float
    demo: bool
    warnings: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    cost_usd: float = 0.0
    ai_shots: list[int] = field(default_factory=list)
    qc: list[dict] = field(default_factory=list)
    qc_summary: str = ""
    format: str = "fakten"
    episode: int = 0
    series_id: str = ""
    next_teaser: str = ""
    music: str = ""


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


# ------------------------------------------------------------------ 1. Skript planen

def plan_story(fmt: str, idea: str, cfg: Config, seconds: int | None = None, series_id: str | None = None,
               choice: str | None = None, fact_check: bool = True, ai_moments: int = 3, demo: bool = False,
               progress: ProgressFn | None = None) -> tuple[Story, list]:
    """Erstellt das Skript und prüft es. Gibt (Story, Prüfpunkte) zurück."""
    report = progress or (lambda p, m: None)
    spec = get_format(fmt)
    seconds = seconds or spec.default_seconds
    series = load_series(series_id) if series_id else None
    episode = len(series.get("episodes", [])) + 1 if series else 0
    use_claude = bool(cfg.anthropic_api_key) and not demo

    def make(attempt: int) -> Story:
        if use_claude:
            if spec.key == "fakten":
                report(_scale(STEP_STORY, 0.1), "Recherchiere Fakten im Web und prüfe sie …" if fact_check
                       else "Skript wird geschrieben …")
                st = generate_story(idea, cfg, seconds, fact_check=fact_check, ai_moments=ai_moments)
                st.format = "fakten"
            else:
                report(_scale(STEP_STORY, 0.2), f"Claude schreibt „{spec.name}“" + (f", Folge {episode}" if episode else "") + " …")
                st = generate_format_story(spec.key, idea, cfg, seconds, series, choice)
            ledger.record("claude", st.script_cost_usd, f"Skript: {st.title}")
            return st
        report(_scale(STEP_STORY, 0.3), f"Kostenloser Generator: „{spec.name}“" + (f", Folge {episode}" if episode else "") + " …")
        return generate_offline(spec.key, seconds, idea, episode, series, seed=None, choice=choice)

    story, checks = None, []
    for attempt in range(3 if not use_claude else 2):   # Claude: höchstens 1 Neuversuch (kostet)
        story = make(attempt)
        checks = qc.check_script(story, spec, series)
        if not any(c.status == "fail" for c in checks):
            break
        report(_scale(STEP_STORY, 0.6), "Qualitätskontrolle: Skript wird verbessert …")
    if any(c.status == "fail" for c in checks):
        problems = "; ".join(c.detail for c in checks if c.status == "fail")
        raise StoryError(f"❌ Das Skript hat die Qualitätskontrolle nicht bestanden: {problems}")
    story.episode = episode or story.episode
    if series:
        story.series_id, story.series_name = series["id"], series["name"]
    report(STEP_STORY[1], f"Skript fertig: „{story.title}“ ({len(story.scenes)} Szenen)")
    return story, checks


# ------------------------------------------------------------------ 2. Rendern

def render_story(story: Story, cfg: Config, progress: ProgressFn | None = None, mode: str = "stock",
                 ai_moments: int = 3, voice: str | None = None, voice_style: str | None = None,
                 music_style: str | None = None, subtitle_style: str | None = None,
                 script_checks: list | None = None, demo: bool = False) -> VideoResult:
    report = progress or (lambda p, msg: print(f"[{p:3d}%] {msg}"))
    spec = get_format(story.format)
    reset_tts_state()
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(story.title)}"
    work_dir = cfg.cache_dir / run_id

    # ② Stimmen: Erzähler im gewählten Stil, Figuren mit eigenen Stimmen
    narrator = voice or cfg.voice
    style = VOICE_STYLES.get(voice_style or spec.voice_style, VOICE_STYLES["normal"])
    char_voices = assign_voices(story.characters, narrator)
    for c in story.characters:
        c.voice = char_voices.get(c.name, "")
    voices = []
    for i, scene in enumerate(story.scenes):
        report(_scale(STEP_VOICE, i / len(story.scenes)), f"KI-Stimme spricht Szene {i + 1} von {len(story.scenes)} …")
        v = char_voices.get(scene.speaker) if scene.speaker else None
        rate = style["rate"] if not v else "+3%"
        if i == 0 and (voice_style or spec.voice_style) == "normal":
            rate = "-4%"                       # Hook etwas langsamer und eindringlicher
        voices.append(synthesize(scene.text, work_dir / f"voice_{i:02d}.mp3", cfg, rate=rate,
                                 voice=v or narrator, pitch=style["pitch"] if not v else "+0Hz"))

    # ③ Bildmaterial – im Hybrid-Modus bekommen die wichtigsten Momente KI-Szenen
    ai_flags = pick_ai_moments(story.scenes, ai_moments) if mode != "stock" else [False] * len(story.scenes)
    media = []
    for i, (scene, flag) in enumerate(zip(story.scenes, ai_flags)):
        report(_scale(STEP_MEDIA, i / len(story.scenes)), f"Bild für Szene {i + 1}: {scene.kind} …")
        media.append(get_shot_media(scene, cfg, work_dir / "media", mode=mode, is_ai_moment=flag,
                                    story=story, spec=spec, index=i))

    # ④–⑥ Schnitt, Grafiken, Untertitel, Ton, Export
    report(STEP_RENDER[0], "Schnitt, Grafiken, Untertitel, Musik und Effekte werden eingefügt …")
    out_path = cfg.output_dir / f"{run_id}.mp4"
    checks = list(script_checks or [])
    for attempt in range(2):                       # bei defekter Datei einmal neu rendern
        _, info = build_video(story, voices, media, out_path, cfg, logger=_RenderProgress(report),
                              subtitle_style=subtitle_style, music_style=music_style)
        report(_scale(STEP_QC, 0.3), "Qualitätskontrolle: Datei, Bild und Ton werden geprüft …")
        file_checks = qc.check_mp4(out_path, info.duration, cfg.size)
        if not any(c.status == "fail" for c in file_checks) or attempt == 1:
            break
        report(STEP_RENDER[0], "Qualitätskontrolle: Datei fehlerhaft – wird neu gerendert …")
    checks += qc.check_render(info, voices) + file_checks

    caption = f"{story.title} " + " ".join(f"#{h.lstrip('#')}" for h in story.hashtags)
    out_path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    out_path.with_suffix(".json").write_text(story.model_dump_json(indent=2), encoding="utf-8")

    warnings = []
    if any(v.silent for v in voices):
        warnings.append("Die KI-Stimme war nicht erreichbar (Internetverbindung?) – das Video hat keine Sprachausgabe.")
    if spec.look == "stock" and not cfg.pexels_api_key:
        warnings.append("Ohne Pexels-Schlüssel werden generierte Hintergründe statt echter Videoclips verwendet.")
    if mode == "preview":
        warnings.append(f"Hybrid-Vorschau: Die {sum(ai_flags)} markierten Szenen würden später KI-Szenen. Noch wurde nichts bezahlt.")
    if demo or not cfg.anthropic_api_key:
        warnings.append("Kostenloser Modus: Das Skript stammt aus dem Offline-Generator (deine Idee fließt erst mit "
                        "Claude-Schlüssel ein)." if spec.key != "fakten" else
                        "Testmodus ohne Claude: Es wurde das Demo-Skript zur Erdrotation verwendet, nicht dein Thema.")

    # Serie fortschreiben
    if story.series_id:
        try:
            series = load_series(story.series_id)
            record_episode(series, story, out_path.name, extra=getattr(story, "_extra", {}) or {})
        except (FileNotFoundError, ValueError):
            warnings.append("Serie konnte nicht gespeichert werden.")

    report(100, "Fertig!")
    return VideoResult(out_path, story.title, caption, info.duration, demo or not cfg.anthropic_api_key, warnings,
                       [s.model_dump() for s in story.sources], round(story.script_cost_usd, 4),
                       [i + 1 for i, f in enumerate(ai_flags) if f], [c.dict() for c in checks],
                       qc.summarize(checks), story.format, story.episode, story.series_id, story.next_teaser,
                       info.music)


def make_video(topic: str, cfg: Config, seconds: int | None = None, progress: ProgressFn | None = None,
               demo: bool = False, fact_check: bool = True, mode: str = "stock", ai_moments: int = 3,
               fmt: str = "fakten", series_id: str | None = None, choice: str | None = None,
               voice: str | None = None, voice_style: str | None = None, music_style: str | None = None,
               subtitle_style: str | None = None) -> VideoResult:
    """Planen + Rendern in einem Schritt."""
    story, checks = plan_story(fmt, topic, cfg, seconds, series_id, choice, fact_check, ai_moments, demo, progress)
    return render_story(story, cfg, progress, mode, ai_moments, voice, voice_style, music_style, subtitle_style,
                        checks, demo)
