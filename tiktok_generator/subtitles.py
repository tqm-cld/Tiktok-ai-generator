"""Schritt 4: Animierte Untertitel im TikTok-Stil.

- Es werden immer 2-3 Wörter gleichzeitig gezeigt.
- Das gerade gesprochene Wort leuchtet gelb.
- Jede neue Wortgruppe "ploppt" kurz auf (wird kurz größer).

Die Untertitel werden mit Pillow als transparente Bilder gezeichnet.
So braucht man kein zusätzliches Programm wie ImageMagick.
"""

from functools import lru_cache
from pathlib import Path

import numpy as np
from moviepy import ImageClip
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import Config
from .voice import Word

WHITE = (255, 255, 255, 255)
HIGHLIGHT = (255, 221, 0, 255)      # gerade gesprochenes Wort
EMPHASIS = (255, 70, 120, 255)      # besonders wichtiges Wort (vom Skript markiert)
OUTLINE = (0, 0, 0, 255)

# Untertitelstile (in der App auswählbar)
STYLES = {
    "tiktok": {"name": "TikTok (weiß/gelb)", "upper": True, "base": WHITE, "active": HIGHLIGHT, "emph": EMPHASIS,
               "stroke": OUTLINE, "box": None, "glow": None, "size": 1.0},
    "mystery": {"name": "Mystery (rot)", "upper": True, "base": (238, 238, 238, 255), "active": (255, 82, 82, 255),
                "emph": (120, 210, 255, 255), "stroke": OUTLINE, "box": None, "glow": (255, 40, 40), "size": 0.95},
    "clean": {"name": "Klar mit Hintergrund", "upper": False, "base": WHITE, "active": (255, 214, 64, 255),
              "emph": (255, 140, 90, 255), "stroke": None, "box": (10, 10, 16, 200), "glow": None, "size": 0.9},
    "neon": {"name": "Neon (türkis)", "upper": True, "base": WHITE, "active": (37, 244, 238, 255),
             "emph": (255, 60, 200, 255), "stroke": (8, 8, 20, 255), "box": None, "glow": (37, 200, 255), "size": 1.0},
}
CAPTION_CENTER_X = 0.45   # etwas links der Mitte: rechts liegt TikToks Like-/Kommentar-Leiste
CAPTION_WIDTH = 0.74

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",          # Linux
    "/Library/Fonts/Arial Bold.ttf",                                  # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",              # macOS
    "C:/Windows/Fonts/arialbd.ttf",                                   # Windows
]


@lru_cache(maxsize=8)
def load_font(fonts_dir: str, size: int) -> ImageFont.FreeTypeFont:
    # Eigene Schriftarten (.ttf) in assets/fonts haben Vorrang.
    own = sorted(Path(fonts_dir).glob("*.ttf")) + sorted(Path(fonts_dir).glob("*.otf"))
    for path in [*map(str, own), *FONT_CANDIDATES]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def group_words(words: list[Word], per_group: int) -> list[list[Word]]:
    """Teilt die Wörter in kleine Gruppen. Nach Satzzeichen beginnt eine neue Gruppe."""
    groups, current = [], []
    for w in words:
        current.append(w)
        if len(current) >= per_group or w.text.rstrip().endswith((".", "!", "?", ",", ":")):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _clean(word: str) -> str:
    return word.strip(".,!?:;–-\"'„“”").lower()


def _render(group: list[Word], active: int, font, max_width: int, emphasis: set[str] = frozenset(),
            style: dict | None = None) -> Image.Image:
    """Zeichnet eine Wortgruppe; das Wort mit Index `active` wird hervorgehoben."""
    style = style or STYLES["tiktok"]
    texts = [w.text.upper() if style["upper"] else w.text for w in group]
    stroke = max(4, font.size // 12) if style["stroke"] else 0
    space = font.getlength(" ")

    # Wörter auf Zeilen verteilen, falls die Breite nicht reicht
    lines, line, line_w = [], [], 0.0
    for i, t in enumerate(texts):
        tw = font.getlength(t)
        if line and line_w + space + tw > max_width:
            lines.append(line)
            line, line_w = [], 0.0
        line.append((i, t, tw))
        line_w += tw + (space if len(line) > 1 else 0)
    lines.append(line)

    ascent, descent = font.getmetrics()
    pad = 26 if style["box"] else 12
    line_h = ascent + descent + stroke * 2
    img_h = line_h * len(lines) + stroke * 2 + pad * 2
    img = Image.new("RGBA", (max_width + stroke * 4 + pad * 2, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if style["box"]:
        widest = max(sum(tw for _, _, tw in items) + space * (len(items) - 1) for items in lines)
        bx0 = (img.width - widest) / 2 - pad
        draw.rounded_rectangle([bx0, 0, bx0 + widest + pad * 2, img_h - 1], radius=22, fill=style["box"])
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0)) if style["glow"] else None
    gdraw = ImageDraw.Draw(glow) if glow else None

    for row, items in enumerate(lines):
        total = sum(tw for _, _, tw in items) + space * (len(items) - 1)
        x = (img.width - total) / 2
        y = pad + stroke + row * line_h
        for i, t, tw in items:
            color = style["active"] if i == active else (style["emph"] if _clean(group[i].text) in emphasis else style["base"])
            if gdraw and i == active:
                gdraw.text((x, y), t, font=font, fill=style["glow"] + (255,), stroke_width=stroke + 6,
                           stroke_fill=style["glow"] + (255,))
            draw.text((x, y), t, font=font, fill=color, stroke_width=stroke,
                      stroke_fill=style["stroke"] if style["stroke"] else None)
            x += tw + space
    if glow is not None:
        base = glow.filter(ImageFilter.GaussianBlur(12))
        base.alpha_composite(img)
        img = base
    return img


def make_subtitle_clips(words: list[Word], duration: float, cfg: Config,
                        emphasis: set[str] = frozenset(), style: str = "tiktok") -> list[ImageClip]:
    """Erzeugt viele kleine Untertitel-Clips (einen pro Wort), die genau dann erscheinen,
    wenn das Wort gesprochen wird. Position: sichere Zone (nicht unter TikToks Bedienelementen)."""
    st = STYLES.get(style, STYLES["tiktok"])
    font = load_font(str(cfg.fonts_dir), int(cfg.font_size * st["size"]))
    max_width = int(cfg.width * CAPTION_WIDTH)
    groups = group_words(words, cfg.words_per_caption)
    center_y = int(cfg.height * cfg.caption_y)
    center_x = int(cfg.width * CAPTION_CENTER_X)

    clips = []
    for gi, group in enumerate(groups):
        # Die Gruppe bleibt sichtbar, bis die nächste beginnt.
        group_start = group[0].start
        group_end = groups[gi + 1][0].start if gi + 1 < len(groups) else duration
        for wi, word in enumerate(group):
            start = word.start
            end = group[wi + 1].start if wi + 1 < len(group) else group_end
            if end <= start:
                continue
            image = np.array(_render(group, wi, font, max_width, emphasis, st))
            h, w = image.shape[:2]
            clip = ImageClip(image).with_start(start).with_duration(end - start)

            if wi == 0:
                # "Pop"-Animation: neue Gruppe wächst in 0,12 s von 80 % auf 100 %
                def scale(t):
                    return 0.8 + 0.2 * min(1.0, t / 0.12)

                def position(t, w=w, h=h):
                    s = scale(t)
                    return (center_x - w * s / 2, center_y - h * s / 2)

                clip = clip.resized(scale).with_position(position)
            else:
                clip = clip.with_position((center_x - w // 2, center_y - h // 2))
            clips.append(clip)
    return clips
