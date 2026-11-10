"""Schritt 6: Alles zu einem 9:16-Video zusammensetzen.

Aufbau des fertigen Videos (von unten nach oben):
  1. Hintergrund (ein Clip/Bild pro Szene, mit langsamem Zoom bei Bildern)
     (leicht abgedunkelt, damit die Schrift gut lesbar ist)
  2. animierte Untertitel
  + Ton: KI-Stimme + leise Hintergrundmusik
"""

from pathlib import Path

import numpy as np
from PIL import Image

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)

from .config import Config
from .media import is_video
from .music import music_clip, pick_music
from .subtitles import make_subtitle_clips
from .voice import VoiceClip, Word

PAUSE_BETWEEN_SCENES = 0.25  # Sekunden Stille zwischen zwei Szenen
DARKEN = 0.75                # 1.0 = Original-Helligkeit, kleiner = dunkler


def _darken(frame):
    return (frame * DARKEN).astype("uint8")


def _fill_frame(clip, cfg: Config):
    """Skaliert einen Clip so, dass er das 9:16-Bild komplett füllt, und schneidet den Rest ab."""
    scale = max(cfg.width / clip.w, cfg.height / clip.h)
    clip = clip.resized(scale)
    return clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=cfg.width, height=cfg.height)


def background_for_scene(media: Path, duration: float, cfg: Config):
    if is_video(media):
        clip = VideoFileClip(str(media), audio=False)
        if clip.duration < duration:
            clip = clip.with_effects([vfx.Loop(duration=duration)])
        clip = _fill_frame(clip.subclipped(0, duration), cfg)
        return clip.image_transform(_darken)

    # Standbild → "Ken-Burns-Effekt": langsam hineinzoomen (insgesamt ca. 12 %)
    still = _fill_frame(ImageClip(str(media)), cfg).get_frame(0)
    picture = Image.fromarray(_darken(still[:, :, :3]))
    W, H = cfg.size

    def zoom_frame(t):
        zoom = 1.0 + 0.12 * (t / duration)
        cw, ch = W / zoom, H / zoom
        box = ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)
        return np.asarray(picture.resize((W, H), Image.BILINEAR, box=box))

    return VideoClip(zoom_frame, duration=duration)


def build_video(voice_clips: list[VoiceClip], media_files: list[Path], out_path: Path, cfg: Config,
                logger="bar") -> Path:
    """Setzt das Video zusammen. `logger` kann den Render-Fortschritt empfangen."""
    backgrounds, audios, all_words = [], [], []
    t = 0.0
    for voice, media in zip(voice_clips, media_files):
        scene_len = voice.duration + PAUSE_BETWEEN_SCENES
        backgrounds.append(background_for_scene(media, scene_len, cfg))
        audios.append(AudioFileClip(str(voice.path)).with_start(t))
        # Wortzeiten von "innerhalb der Szene" auf "im ganzen Video" verschieben
        all_words += [Word(w.text, w.start + t, w.end + t) for w in voice.words]
        t += scene_len

    total = t
    if total > cfg.max_seconds:
        print(f"  ⚠ Das Video ist {total:.0f}s lang (Ziel: max. {cfg.max_seconds}s).")
    elif total < cfg.min_seconds:
        print(f"  ⚠ Das Video ist nur {total:.0f}s lang (Ziel: min. {cfg.min_seconds}s).")

    # "chain" ist schnell, weil alle Szenen schon genau 1080x1920 groß sind
    background = concatenate_videoclips(backgrounds, method="chain").with_duration(total)
    subtitles = make_subtitle_clips(all_words, total, cfg)

    video = CompositeVideoClip([background, *subtitles], size=cfg.size, use_bgclip=True).with_duration(total)

    # Ton mischen
    sound = [*audios]
    track = pick_music(cfg)
    if track:
        print(f"  ♪ Musik: {track.name}")
        sound.append(music_clip(track, total, cfg))
    else:
        print("  ℹ Keine Musik in assets/music gefunden → Video ohne Musik.")
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
        ffmpeg_params=["-pix_fmt", "yuv420p"],  # damit es auf allen Handys abspielt
        logger=logger,
    )
    video.close()
    return out_path

