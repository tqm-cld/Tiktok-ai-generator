"""Schritt 6: Alles zu einem dynamischen 9:16-Video zusammensetzen.

Aufbau:
  1. Hintergrund: pro Szene ein Clip/Bild, aufgeteilt in kurze Einstellungen (ca. 2-3 s) mit
     Kamerafahrt (Heranzoomen, Herauszoomen, Schwenk). An jedem Schnitt ein kurzer "Zoom-Schlag",
     bei Schock-Momenten zusätzlich Lichtblitz und Wackeln.
  2. Hook-Titel groß oben in den ersten Sekunden
  3. wortgenaue animierte Untertitel
  + Ton: KI-Stimme, Soundeffekte, Hintergrundmusik
"""

import math
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw

from .config import Config
from .media import is_video
from .music import music_clip, pick_music
from .sfx import ambient_music, effect_clip
from .subtitles import load_font, make_subtitle_clips
from .voice import VoiceClip, Word

PAUSE_BETWEEN_SCENES = 0.15  # kurze Pausen = schnelles Tempo
DARKEN = 0.72                # 1.0 = Original-Helligkeit, kleiner = dunkler (bessere Lesbarkeit)
MAX_CUT_SECONDS = 3.2        # längere Szenen werden in mehrere Einstellungen geschnitten
HOOK_SECONDS = 2.8
MOTIONS = ["push", "pan_r", "pull", "pan_l"]
SHOCK_SFX = {"impact", "boom"}


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


def _cut_clip(source: _Source, offset: float, duration: float, motion: str, shock: bool, cfg: Config):
    """Eine Einstellung mit Kamerafahrt. Füllen + Zoomen + Schwenken in EINEM Rechenschritt."""
    W, H = cfg.size
    sw, sh = source.size
    fill = max(W / sw, H / sh)                      # so weit vergrößern, dass 9:16 gefüllt ist
    rng = np.random.default_rng(int(offset * 1000) + len(motion))
    phase = rng.uniform(0, 6.28)

    def make_frame(t):
        p = t / max(duration, 0.01)
        ease = p * p * (3 - 2 * p)                   # sanft beschleunigen/abbremsen
        if motion == "push":
            zoom, pan = 1.04 + 0.14 * ease, 0.0
        elif motion == "pull":
            zoom, pan = 1.18 - 0.14 * ease, 0.0
        else:
            zoom, pan = 1.16, (ease - 0.5) * 0.10 * (1 if motion == "pan_r" else -1)
        zoom *= 1 + 0.07 * math.exp(-t * 16)         # Zoom-Schlag direkt nach dem Schnitt

        dx = dy = 0.0
        if shock:                                    # Wackeln bei Schock-Momenten
            amp = 22 * math.exp(-t * 6)
            dx, dy = amp * math.sin(t * 55 + phase), amp * math.cos(t * 47 + phase)

        cw, ch = W / (fill * zoom), H / (fill * zoom)  # sichtbarer Ausschnitt im Original
        cx = sw / 2 + pan * sw + dx / fill
        cy = sh / 2 + dy / fill
        cx = min(max(cx, cw / 2), sw - cw / 2)
        cy = min(max(cy, ch / 2), sh - ch / 2)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        img = source.frame(offset + t).resize((W, H), Image.BILINEAR, box=box)
        frame = np.asarray(img, dtype=np.float32) * DARKEN

        if shock:                                    # kurzer weißer Lichtblitz
            flash = 0.75 * math.exp(-t * 18)
            if flash > 0.02:
                frame = frame * (1 - flash) + 255 * flash
        return frame.astype(np.uint8)

    return VideoClip(make_frame, duration=duration)


def _scene_cuts(scene_len: float) -> list[float]:
    n = max(1, math.ceil(scene_len / MAX_CUT_SECONDS))
    return [scene_len / n] * n


def _hook_clips(text: str, cfg: Config) -> list:
    """Großer Hook-Titel oben, ploppt auf und verschwindet nach ein paar Sekunden."""
    if not text:
        return []
    font = load_font(str(cfg.fonts_dir), int(cfg.font_size * 1.25))
    words, lines, line = text.upper().split(), [], ""
    for w in words:                                   # Zeilenumbruch nach Breite
        test = f"{line} {w}".strip()
        if line and font.getlength(test) > cfg.width * 0.84:
            lines.append(line)
            line = w
        else:
            line = test
    lines.append(line)

    stroke = 7
    asc, desc = font.getmetrics()
    lh = asc + desc + 10
    width = int(max(font.getlength(l) for l in lines)) + 80
    img = Image.new("RGBA", (width, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=28, fill=(255, 45, 111, 235))
    for i, l in enumerate(lines):
        x = (img.width - font.getlength(l)) / 2
        d.text((x, 20 + i * lh), l, font=font, fill="white", stroke_width=stroke, stroke_fill=(0, 0, 0))

    arr = np.array(img)
    h, w = arr.shape[:2]
    top = int(cfg.height * 0.14)

    def scale(t):
        s = 0.6 + 0.4 * min(1.0, t / 0.18)
        return s * (1 + 0.04 * math.sin(min(1.0, t / 0.18) * math.pi))  # kleiner Überschwinger

    def pos(t):
        s = scale(t)
        return ((cfg.width - w * s) / 2, top - h * s / 2 + h / 2)

    clip = ImageClip(arr).with_duration(HOOK_SECONDS).resized(scale).with_position(pos)
    return [clip.with_start(0)]


def build_video(voice_clips: list[VoiceClip], media_files: list[Path], out_path: Path, cfg: Config,
                logger="bar", scenes=None, hook_title: str = "") -> Path:
    """Setzt das Video zusammen. `scenes` liefert Soundeffekte und Betonungswörter."""
    backgrounds, sound, all_words, emphasis = [], [], [], set()
    sources = []
    t = 0.0
    for i, (voice, media) in enumerate(zip(voice_clips, media_files)):
        scene = scenes[i] if scenes else None
        scene_len = voice.duration + PAUSE_BETWEEN_SCENES
        source = _Source(media)
        sources.append(source)
        sfx = getattr(scene, "sfx", "none") or "none"

        offset, cut_start = 0.0, t
        for k, cut_len in enumerate(_scene_cuts(scene_len)):
            motion = MOTIONS[(i + k) % len(MOTIONS)]
            shock = k == 0 and sfx in SHOCK_SFX
            backgrounds.append(_cut_clip(source, offset, cut_len, motion, shock, cfg))
            # Wisch-Geräusch an jedem Schnitt (außer ganz am Anfang und wo ein anderer Effekt läuft)
            if cut_start > 0 and not (k == 0 and sfx != "none"):
                sound.append(effect_clip("whoosh", cut_start - 0.2, volume=0.35))
            offset += cut_len + 1.3                    # andere Stelle im Clip zeigen
            cut_start += cut_len

        if sfx != "none":
            sound.append(effect_clip(sfx, t, volume=0.8))
        sound.append(AudioFileClip(str(voice.path)).with_start(t))
        all_words += [Word(w.text, w.start + t, w.end + t) for w in voice.words]
        if scene and getattr(scene, "emphasis", ""):
            emphasis.add(scene.emphasis.strip(".,!?:;–-\"'").lower())
        t += scene_len

    total = t
    if total > cfg.max_seconds:
        print(f"  ⚠ Das Video ist {total:.0f}s lang (Ziel: max. {cfg.max_seconds}s).")
    elif total < cfg.min_seconds:
        print(f"  ⚠ Das Video ist nur {total:.0f}s lang (Ziel: min. {cfg.min_seconds}s).")

    background = concatenate_videoclips(backgrounds, method="chain").with_duration(total)
    overlays = _hook_clips(hook_title, cfg) + make_subtitle_clips(all_words, total, cfg, emphasis)
    video = CompositeVideoClip([background, *overlays], size=cfg.size, use_bgclip=True).with_duration(total)

    track = pick_music(cfg)
    if track:
        print(f"  ♪ Musik: {track.name}")
        sound.append(music_clip(track, total, cfg))
    else:
        print("  ♪ Keine eigene Musik → erzeuge Doku-Klangteppich.")
        sound.append(ambient_music(total).with_effects([afx.MultiplyVolume(cfg.music_volume * 1.4)]))
    video = video.with_audio(CompositeAudioClip(sound).with_duration(total))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(
        str(out_path),
        fps=cfg.fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        temp_audiofile=str(out_path.with_suffix(".temp.m4a")),
        ffmpeg_params=["-pix_fmt", "yuv420p", "-crf", "20"],  # gute Qualität, auf allen Handys abspielbar
        logger=logger,
    )
    video.close()
    for s in sources:
        s.close()
    return out_path
