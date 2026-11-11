"""Schritt 6: Alles zu einem 9:16-Video (1080 × 1920) zusammensetzen.

Ebenen (von unten nach oben):
  1. Kulisse/Clip je Szene, in Einstellungen von max. ~3 s geschnitten, mit format-typischer
     Kameraführung (Überwachungskamera: fest mit Detail-Zoom, Level: langsames Vorwärtsgleiten, …)
     und Farbstimmung (CCTV: grünliches Schwarzweiß mit Rauschen und Zeilen).
  2. Format-Grafiken (Figuren, Aussagen, Hinweise, Countdown, Auswahl, Regeln …) – overlays.py
  3. Hook-Titel, Folgen-Etikett, wortgenaue Untertitel im gewählten Stil
  + Ton: Stimmen (Erzähler + Figuren), Soundeffekte im Takt, Musik mit Ducking, Limiter
"""

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from moviepy import AudioArrayClip, AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, \
    concatenate_videoclips
from PIL import Image, ImageDraw

from .audio import RATE, generate_music, load_user_music, mix
from .config import Config
from .formats import get_format
from .media import is_video
from .overlays import OverlayContext, episode_badge, hook_title, scene_overlays
from .sfx import EFFECTS, countdown as countdown_fx
from .subtitles import load_font, make_subtitle_clips
from .voice import VoiceClip, Word

PAUSE_BETWEEN_SCENES = 0.15  # kurze Pausen = schnelles Tempo
MAX_CUT_SECONDS = 3.2        # spätestens alle ~3 s ändert sich das Bild
HOOK_SECONDS = 2.6
STOCK_DARKEN = 0.72          # Stockvideos abdunkeln, damit Schrift lesbar bleibt
MOTIONS = {
    "stock": ["push", "pan_r", "pull", "pan_l"],
    "landscape": ["pan_r", "push", "pan_l", "pull"],
    "lineup": ["push", "pull", "push", "pan_r"],
    "board": ["pan_l", "push", "pan_r", "pull"],
    "corridor": ["dolly", "dolly", "dolly", "dolly"],
    "cctv": ["static", "detail", "static", "detail"],
}


class _Source:
    """Liefert Einzelbilder aus einem Video oder Standbild (Video wird bei Bedarf wiederholt)."""

    def __init__(self, media: Path):
        self.video = VideoFileClip(str(media), audio=False) if is_video(media) else None
        self.still = None if self.video else Image.open(media).convert("RGB")
        self.size = self.video.size if self.video else self.still.size

    def frame(self, t: float) -> Image.Image:
        if self.still is not None:
            return self.still
        dur = max(0.1, self.video.duration - 0.05)
        return Image.fromarray(self.video.get_frame(t % dur))

    def close(self):
        if self.video:
            self.video.close()


class _Grader:
    """Farbstimmung je Bildstil (vorberechnetes Rauschen/Zeilen für Tempo)."""

    def __init__(self, look: str, size, seed=3):
        self.look = look
        W, H = size
        rng = np.random.default_rng(seed)
        self.noise = [rng.normal(0, 1, (H, W, 1)).astype(np.float32) for _ in range(4)] \
            if look in ("cctv", "corridor") else None
        if look == "cctv":
            rows = np.ones((H, 1, 1), dtype=np.float32)
            rows[::4] = 0.80
            self.scan = rows
            yy, xx = np.mgrid[0:H, 0:W]
            r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
            self.vig = np.clip(1.15 - 0.45 * r, 0.45, 1)[..., None].astype(np.float32)

    def __call__(self, frame: np.ndarray, t: float) -> np.ndarray:
        if self.look == "stock":
            return frame * STOCK_DARKEN
        if self.look == "cctv":
            lum = frame[..., 0:1] * 0.299 + frame[..., 1:2] * 0.587 + frame[..., 2:3] * 0.114
            out = lum * np.array([0.80, 1.0, 0.82], dtype=np.float32)
            out = out * self.scan * self.vig + self.noise[int(t * 12) % 4] * 14
            return out * 0.92
        if self.look == "corridor":
            return frame * np.array([1.03, 1.0, 0.90], dtype=np.float32) + self.noise[int(t * 12) % 4] * 5
        if self.look == "board":
            return frame * np.array([1.04, 0.98, 0.90], dtype=np.float32)
        if self.look == "lineup":
            return frame * np.array([0.98, 1.0, 1.05], dtype=np.float32)
        return frame


def _cut_clip(source: _Source, offset: float, duration: float, motion: str, shock: bool, cfg: Config,
              grade=None, seed: int = 0):
    """Eine Einstellung mit Kamerafahrt. Füllen + Zoomen + Schwenken in EINEM Rechenschritt."""
    W, H = cfg.size
    sw, sh = source.size
    fill = max(W / sw, H / sh)                      # so weit vergrößern, dass 9:16 gefüllt ist
    rng = np.random.default_rng(seed)
    phase = rng.uniform(0, 6.28)
    detail = (rng.uniform(-0.12, 0.12), rng.uniform(-0.10, 0.05))   # Bildausschnitt beim Detail-Zoom

    def make_frame(t):
        p = t / max(duration, 0.01)
        ease = p * p * (3 - 2 * p)                   # sanft beschleunigen/abbremsen
        pan_x = pan_y = 0.0
        if motion == "ai":                           # KI-Clip bewegt sich selbst → nur sanft zoomen
            zoom = 1.02 + 0.05 * ease
        elif motion == "push":
            zoom = 1.04 + 0.12 * ease
        elif motion == "pull":
            zoom = 1.16 - 0.12 * ease
        elif motion == "dolly":                      # langsames Vorwärtsgleiten durch den Gang
            zoom = 1.0 + 0.10 * p
        elif motion == "static":                     # feste Überwachungskamera
            zoom = 1.0
        elif motion == "detail":                     # digitaler Zoom auf einen Bildbereich
            zoom = 1.22
            pan_x, pan_y = detail
        else:
            zoom = 1.14
            pan_x = (ease - 0.5) * 0.10 * (1 if motion == "pan_r" else -1)
        if motion not in ("static", "detail", "dolly"):
            zoom *= 1 + 0.035 * math.exp(-t * 16)    # dezenter Zoom-Schlag direkt nach dem Schnitt

        dx = dy = 0.0
        if shock:                                    # leichtes Wackeln bei Schock-Momenten
            amp = 8 * math.exp(-t * 7)
            dx, dy = amp * math.sin(t * 55 + phase), amp * math.cos(t * 47 + phase)

        cw, ch = W / (fill * zoom), H / (fill * zoom)  # sichtbarer Ausschnitt im Original
        cx = sw / 2 + pan_x * sw + dx / fill
        cy = sh / 2 + pan_y * sh + dy / fill
        cx = min(max(cx, cw / 2), sw - cw / 2)
        cy = min(max(cy, ch / 2), sh - ch / 2)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        img = source.frame(offset + t).resize((W, H), Image.BILINEAR, box=box)
        frame = np.asarray(img, dtype=np.float32)
        if grade is not None:
            frame = grade(frame, t)
        if shock:                                    # dezentes Aufhellen statt grellem Blitz
            flash = 0.22 * math.exp(-t * 14)
            if flash > 0.02:
                frame = frame * (1 - flash) + 255 * flash
        return np.clip(frame, 0, 255).astype(np.uint8)

    return VideoClip(make_frame, duration=duration)


def _scene_cuts(scene_len: float) -> list[float]:
    n = max(1, math.ceil(scene_len / MAX_CUT_SECONDS))
    return [scene_len / n] * n


def _badge_clip(text: str, start: float, duration: float, cfg: Config):
    """Kleines Etikett, z. B. „KI-SZENE · VORSCHAU“ im Hybrid-Vorschaumodus."""
    font = load_font(str(cfg.fonts_dir), 38)
    w = int(font.getlength(text)) + 44
    img = Image.new("RGBA", (w, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 63], radius=32, fill=(37, 244, 238, 230))
    d.text((22, 10), text, font=font, fill=(11, 11, 18))
    return ImageClip(np.array(img)).with_start(start).with_duration(duration).with_position(
        (int(cfg.width * 0.06), int(cfg.height * 0.055)))


def _voice_array(path: Path) -> np.ndarray:
    with AudioFileClip(str(path)) as clip:
        arr = clip.to_soundarray(fps=RATE)
    if arr.ndim == 1:
        arr = np.column_stack([arr, arr])
    return arr.astype(np.float32)


@dataclass
class RenderInfo:
    duration: float = 0.0
    scene_spans: list = field(default_factory=list)   # (Start, Ende) je Szene
    words: list = field(default_factory=list)         # alle Wörter mit Videozeit
    mix: object = None
    music: str = ""


def build_video(story, voice_clips: list[VoiceClip], media_files: list, out_path: Path, cfg: Config,
                logger="bar", subtitle_style: str | None = None, music_style: str | None = None,
                write: bool = True):
    """Setzt das Video zusammen und gibt (Pfad, RenderInfo) zurück.

    `media_files` enthält pro Szene einen Pfad oder ein ShotMedia-Objekt (Hybrid-Modus):
    Bei KI-Momenten läuft zuerst der KI-Clip, weitere Schnitte im selben Shot nutzen das Ersatzbild."""
    spec = get_format(story.format)
    look = spec.look
    sub_style = subtitle_style or spec.subtitle_style
    mus_style = music_style or spec.music
    grade = _Grader(look, cfg.size)
    motions = MOTIONS.get(look, MOTIONS["stock"])
    ctx = OverlayContext(story, cfg)

    backgrounds, overlays, effects, voices, spans, all_words, emphasis = [], [], [], [], [], [], set()
    sources, info = [], RenderInfo()
    t = 0.0
    scenes = story.scenes
    for i, (voice, media) in enumerate(zip(voice_clips, media_files)):
        scene = scenes[i]
        scene_len = voice.duration + PAUSE_BETWEEN_SCENES
        primary_path = getattr(media, "primary", media)
        secondary_path = getattr(media, "secondary", None)
        is_ai = getattr(media, "ai", False)
        source = _Source(primary_path)
        sources.append(source)
        backup = _Source(secondary_path) if secondary_path else None
        if backup:
            sources.append(backup)
        if getattr(media, "planned_ai", False):
            overlays.append(_badge_clip("KI-SZENE · VORSCHAU", t, scene_len, cfg))
        sfx = scene.sfx or "none"
        shock = scene.kind in ("hook", "reveal") and sfx in ("boom", "impact", "reveal")

        offset = 0.0
        for k, cut_len in enumerate(_scene_cuts(scene_len)):
            motion = motions[(i + k) % len(motions)]
            if look == "cctv" and scene.kind in ("countdown", "reveal"):
                motion = "static"                        # feste Kamera, damit die Markierung exakt sitzt
            if is_ai and k == 0:
                backgrounds.append(_cut_clip(source, 0.0, cut_len, "ai", shock, cfg, grade, seed=i * 7 + k))
            elif is_ai and backup:
                backgrounds.append(_cut_clip(backup, offset, cut_len, motion, False, cfg, grade, seed=i * 7 + k))
            else:
                backgrounds.append(_cut_clip(source, offset, cut_len, motion, shock and k == 0, cfg, grade,
                                             seed=i * 7 + k))
            offset += cut_len + 1.3

        # Soundeffekte im Takt der Szene
        if sfx == "countdown":
            tick = countdown_fx()[: int(0.4 * RATE)]
            for n in range(3):
                effects.append((tick, t + n * scene_len / 3, 0.9))
        elif sfx != "none" and sfx in EFFECTS:
            effects.append((EFFECTS[sfx](), t, 0.85))
        elif i > 0 and look in ("stock", "landscape", "lineup", "board"):
            effects.append((EFFECTS["whoosh"](), t - 0.2, 0.35))   # dezenter Übergang beim Szenenwechsel

        overlays += scene_overlays(ctx, scene, i, t, scene_len)
        voices.append((_voice_array(voice.path), t))
        words = [Word(w.text, w.start + t, w.end + t) for w in voice.words]
        all_words += words
        if words:
            spans.append((words[0].start, words[-1].end))
        if scene.emphasis:
            emphasis.add(scene.emphasis.strip(".,!?:;–-\"'").lower())
        info.scene_spans.append((t, t + scene_len))
        t += scene_len

    total = t
    info.duration, info.words = total, all_words
    music = load_user_music(cfg, mus_style, total)
    info.music = f"eigene Musik ({mus_style})" if music is not None else f"selbst komponiert: {mus_style}"
    if music is None:
        music = generate_music(mus_style, total, seed=len(story.title))
    mixed, report = mix(total, voices, spans, effects, music)
    info.mix = report

    background = concatenate_videoclips(backgrounds, method="chain").with_duration(total)
    top = overlays + hook_title(ctx, story.hook_title, HOOK_SECONDS) + episode_badge(ctx) + \
        make_subtitle_clips(all_words, total, cfg, emphasis, sub_style)
    video = CompositeVideoClip([background, *top], size=cfg.size, use_bgclip=True).with_duration(total)
    video = video.with_audio(AudioArrayClip(mixed, fps=RATE).with_duration(total))

    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(
            str(out_path), fps=cfg.fps, codec="libx264", audio_codec="aac", audio_bitrate="192k",
            preset="medium", threads=4, temp_audiofile=str(out_path.with_suffix(".temp.m4a")),
            ffmpeg_params=["-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart"],
            logger=logger,
        )
    video.close()
    for s in sources:
        s.close()
    return out_path, info
