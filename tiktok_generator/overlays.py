"""Grafiken über dem Bild – je nach Szenentyp und Format.

Sichere Zonen (TikTok-Bedienelemente):
  - oben ca. 9 % (Suchleiste), rechts ca. 16 % (Like-/Kommentar-Leiste), unten ca. 24 % (Beschreibung)
  - Grafiken liegen deshalb im Bereich x 6–84 %, y 9–55 %; die Untertitel bei ca. 63 % Höhe.
Animationen sind bewusst ruhig (Einblenden, kurzes Hineingleiten) – kein hektisches Blinken.
"""

import math

import numpy as np
from moviepy import ImageClip, vfx
from PIL import Image, ImageDraw, ImageFilter

from .subtitles import load_font

SAFE_X0, SAFE_X1 = 0.06, 0.84
ACCENTS = {"imposter": (255, 64, 96), "cctv": (70, 255, 140), "entscheidung": (37, 244, 238),
           "krimi": (255, 184, 77), "level": (255, 214, 77), "fakten": (255, 45, 111)}
CHAR_COLORS = [(255, 99, 99), (84, 160, 255), (255, 200, 60), (120, 220, 140), (190, 120, 255), (255, 150, 60)]
PANEL = (16, 16, 24, 222)


def _font(cfg, size, mono=False):
    if mono:
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "C:/Windows/Fonts/consolab.ttf"):
            try:
                from PIL import ImageFont
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return load_font(str(cfg.fonts_dir), size)


def _wrap(text, font, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = f"{line} {w}".strip()
        if line and font.getlength(test) > max_w:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def _clip(img: Image.Image, start, dur, x, y, fade=0.18, slide=0, fade_out=0.12):
    """Bild als Clip: ruhig einblenden, optional von links hineingleiten."""
    arr = np.array(img)
    clip = ImageClip(arr).with_start(start).with_duration(max(0.05, dur))
    if slide:
        clip = clip.with_position(lambda t, x=x, y=y: (x - slide * max(0.0, 1 - t / 0.22) ** 2, y))
    else:
        clip = clip.with_position((x, y))
    fx = []
    if fade:
        fx.append(vfx.CrossFadeIn(min(fade, dur / 3)))
    if fade_out and dur > 0.6:
        fx.append(vfx.CrossFadeOut(fade_out))
    return clip.with_effects(fx) if fx else clip


def _panel(w, h, accent, label=None, cfg=None, paper=False):
    img = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if paper:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=(244, 236, 214, 250), outline=(120, 96, 60), width=3)
    else:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=PANEL, outline=accent + (255,), width=4)
        d.rounded_rectangle([0, 0, 14, h - 1], radius=7, fill=accent + (255,))
    if label and cfg:
        f = _font(cfg, 34)
        tw = f.getlength(label)
        d.rounded_rectangle([34, -2, 34 + tw + 36, 50], radius=14, fill=accent + (255,))
        d.text((52, 6), label, font=f, fill=(12, 12, 16))
    return img, d


def _avatar(size, color, highlight=None, dim=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = tuple(int(c * (0.45 if dim else 1)) for c in color)
    d.ellipse([0, 0, size - 1, size - 1], fill=base + (255,))
    skin = (250, 236, 220) if not dim else (120, 112, 104)
    d.ellipse([size * 0.32, size * 0.16, size * 0.68, size * 0.52], fill=skin + (255,))
    d.pieslice([size * 0.16, size * 0.50, size * 0.84, size * 1.18], 180, 360, fill=skin + (255,))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    if highlight:
        ImageDraw.Draw(out).ellipse([2, 2, size - 3, size - 3], outline=highlight + (255,), width=8)
    return out


class OverlayContext:
    def __init__(self, story, cfg):
        self.story, self.cfg = story, cfg
        self.W, self.H = cfg.size
        self.fmt = story.format
        self.accent = ACCENTS.get(story.format, ACCENTS["fakten"])
        names = [c.name for c in story.characters]
        self.colors = {n: CHAR_COLORS[i % len(CHAR_COLORS)] for i, n in enumerate(names)}
        self.box_w = int(self.W * (SAFE_X1 - SAFE_X0))
        self.x0 = int(self.W * SAFE_X0)
        self.hud = self._hud_plan(story)

    @staticmethod
    def _hud_plan(story):
        """Kamera und Uhrzeit laufen über alle Szenen durch (kein Springen der Anzeige)."""
        plan, cam, hh, mm = [], None, 3, 0
        for s in story.scenes:
            c, _, tm = (s.on_screen or "").partition("·")
            if c.strip().startswith("CAM") and cam is None:
                cam = c.strip()
            try:
                if ":" in tm:
                    hh, mm = (int(x) for x in tm.strip().split(":")[:2])
            except ValueError:
                pass
            plan.append((hh, mm))
        return {"cam": cam or "CAM 01", "times": plan}

    def y(self, frac):
        return int(self.H * frac)


# ------------------------------------------------------------------ Bausteine

def _text_card(ctx, label, text, start, dur, y, size=50, paper=False, rotate=0.0, center=False):
    f = _font(ctx.cfg, size)
    lines = _wrap(text, f, ctx.box_w - 90)[:4]
    lh = int(size * 1.22)
    h = 74 + lh * len(lines) + 30
    img, d = _panel(ctx.box_w, h, ctx.accent if not paper else (200, 40, 40), label, ctx.cfg, paper=paper)
    color = (20, 20, 24) if paper else (245, 245, 248)
    for i, line in enumerate(lines):
        x = (ctx.box_w - f.getlength(line)) / 2 if center else 44
        d.text((x, 70 + i * lh), line, font=f, fill=color)
    if paper and label:
        lf = _font(ctx.cfg, 36)
        d.text((40, 16), label, font=lf, fill=(190, 30, 30))
    if rotate:
        img = img.rotate(rotate, expand=True, resample=Image.BICUBIC)
    return [_clip(img, start, dur, ctx.x0, ctx.y(y), slide=60)]


def _lineup(ctx, start, dur, speaker="", culprit_reveal=False):
    chars = ctx.story.characters[:5]
    if not chars:
        return []
    size = 128 if len(chars) <= 4 else 106
    f = _font(ctx.cfg, 30)
    gap = (ctx.box_w - size * len(chars)) / (len(chars) + 1)
    img = Image.new("RGBA", (ctx.box_w, size + 52), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, c in enumerate(chars):
        x = gap + i * (size + gap)
        is_culprit = culprit_reveal and c.name == ctx.story.culprit
        hl = (255, 50, 70) if is_culprit else (ctx.accent if c.name == speaker else None)
        dim = (culprit_reveal and not is_culprit) or (speaker and c.name != speaker and not culprit_reveal)
        img.alpha_composite(_avatar(size, ctx.colors.get(c.name, CHAR_COLORS[0]), hl, dim), (int(x), 0))
        name = c.name if len(c.name) <= 11 else c.name.split()[-1][:11]
        tw = f.getlength(name)
        d.text((x + (size - tw) / 2, size + 8), name, font=f, fill=(255, 255, 255) if not dim else (150, 150, 150),
               stroke_width=3, stroke_fill=(0, 0, 0))
        if is_culprit:
            sf = _font(ctx.cfg, 28)
            label = "IMPOSTER" if ctx.fmt == "imposter" else "TÄTER"
            lw = sf.getlength(label) + 20
            d.rounded_rectangle([x + (size - lw) / 2, size - 34, x + (size + lw) / 2, size], radius=8, fill=(255, 50, 70))
            d.text((x + (size - lw) / 2 + 10, size - 32), label, font=sf, fill=(255, 255, 255))
    return [_clip(img, start, dur, ctx.x0, ctx.y(0.105), fade=0.15, fade_out=0)]


def _speech(ctx, scene, start, dur, y=0.27, label=None):
    name = scene.speaker or "Erzähler"
    role = next((c.role for c in ctx.story.characters if c.name == scene.speaker), "")
    f = _font(ctx.cfg, 48)
    nf = _font(ctx.cfg, 38)
    quote = f"„{(scene.on_screen or scene.text).strip('„“\"')}“"
    lines = _wrap(quote, f, ctx.box_w - 80)[:4]
    h = 100 + 60 * len(lines) + 24
    color = ctx.colors.get(scene.speaker, ctx.accent)
    img = Image.new("RGBA", (ctx.box_w, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, ctx.box_w - 1, h], radius=28, fill=PANEL, outline=color + (255,), width=4)
    d.polygon([(70, h - 2), (120, h - 2), (80, h + 30)], fill=PANEL)
    avatar = _avatar(70, color)
    img.alpha_composite(avatar, (28, 18))
    d.text((112, 20), name, font=nf, fill=color + (255,))
    if role:
        rf = _font(ctx.cfg, 28)
        d.text((112, 62), role.upper() if not label else label, font=rf, fill=(180, 180, 190))
    for i, line in enumerate(lines):
        d.text((36, 104 + i * 60), line, font=f, fill=(250, 250, 252))
    return [_clip(img, start, dur, ctx.x0, ctx.y(y), slide=70)]


def _countdown(ctx, scene, start, dur):
    clips = []
    try:
        first = max(1, min(9, int((scene.on_screen or "3").strip()[:1])))
    except ValueError:
        first = 3
    numbers = list(range(first, 0, -1))
    step = dur / len(numbers)
    size = 340
    nf = _font(ctx.cfg, 210)
    for i, n in enumerate(numbers):
        img = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([10, 10, size + 10, size + 10], fill=(12, 12, 18, 210))
        d.arc([10, 10, size + 10, size + 10], -90, -90 + 360 * (len(numbers) - i) / len(numbers),
              fill=ctx.accent + (255,), width=18)
        tw = nf.getlength(str(n))
        d.text(((size + 20 - tw) / 2, (size + 20) / 2 - 135), str(n), font=nf, fill=(255, 255, 255))
        x = int(ctx.W * (SAFE_X0 + SAFE_X1) / 2 - (size + 20) / 2)
        clips.append(_clip(img, start + i * step, step, x, ctx.y(0.30), fade=0.08, fade_out=0))
    question = scene.text.split("?")[0] + "?" if "?" in scene.text else ""
    if question:
        f = _font(ctx.cfg, 56)
        lines = _wrap(question.upper(), f, ctx.box_w - 40)
        img = Image.new("RGBA", (ctx.box_w, 70 * len(lines) + 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            d.text(((ctx.box_w - f.getlength(line)) / 2, i * 70), line, font=f, fill=(255, 255, 255),
                   stroke_width=6, stroke_fill=(0, 0, 0))
        clips.append(_clip(img, start, dur, ctx.x0, ctx.y(0.215 if ctx.fmt != "imposter" else 0.235)))
    return clips


def _choices(ctx, scene, start, dur):
    options = [o.strip() for o in (scene.on_screen or " | ".join(ctx.story.choices)).split("|") if o.strip()]
    clips, y = [], 0.15
    f = _font(ctx.cfg, 46)
    lf = _font(ctx.cfg, 64)
    for i, opt in enumerate(options[:3]):
        letter, _, text = opt.partition(":")
        lines = _wrap(text.strip() or opt, f, ctx.box_w - 170)[:2]
        h = 46 + 56 * len(lines)
        img = Image.new("RGBA", (ctx.box_w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, ctx.box_w - 1, h - 1], radius=24, fill=PANEL, outline=ctx.accent + (255,), width=4)
        d.rounded_rectangle([14, 14, 108, h - 14], radius=18, fill=ctx.accent + (255,))
        lt = letter.strip()[:1] or "ABC"[i]
        d.text((61 - lf.getlength(lt) / 2, h / 2 - 40), lt, font=lf, fill=(12, 12, 16))
        for k, line in enumerate(lines):
            d.text((132, 22 + k * 56), line, font=f, fill=(250, 250, 252))
        delay = i * min(0.45, dur / 6)
        clips.append(_clip(img, start + delay, dur - delay, ctx.x0, ctx.y(y), slide=80))
        y += (h + 22) / ctx.H
    return clips


def _level_title(ctx, scene, start, dur):
    top, _, sub = (scene.on_screen or scene.text).partition("|")
    big = _font(ctx.cfg, 150)
    small = _font(ctx.cfg, 54)
    img = Image.new("RGBA", (ctx.box_w, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tw = big.getlength(top.upper())
    scale = min(1.0, (ctx.box_w - 20) / max(1, tw))
    if scale < 1:
        big = _font(ctx.cfg, int(150 * scale))
        tw = big.getlength(top.upper())
    d.text(((ctx.box_w - tw) / 2, 10), top.upper(), font=big, fill=ctx.accent, stroke_width=8, stroke_fill=(0, 0, 0))
    if sub:
        d.text(((ctx.box_w - small.getlength(sub)) / 2, 200), sub, font=small, fill=(255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0))
    return [_clip(img, start, dur, ctx.x0, ctx.y(0.20), fade=0.35)]


def _cctv_hud(ctx, scene, index, start, dur):
    """REC-Anzeige, Kameraname und laufende Uhrzeit (eine Grafik pro Sekunde)."""
    cam = ctx.hud["cam"]
    hh, mm = ctx.hud["times"][index] if index < len(ctx.hud["times"]) else (3, 0)
    f = _font(ctx.cfg, 40, mono=True)
    clips = []
    for sec in range(int(math.ceil(dur))):
        img = Image.new("RGBA", (ctx.box_w, 120), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        on = sec % 2 == 0  # REC-Punkt langsam (1 Hz), kein hektisches Blinken
        d.ellipse([4, 12, 40, 48], fill=(255, 40, 40, 255 if on else 90))
        d.text((54, 8), f"REC  {cam}", font=f, fill=(235, 255, 235))
        d.text((4, 64), f"{hh:02d}:{mm:02d}:{(int(start) + sec) % 60:02d}", font=f, fill=(235, 255, 235))
        clips.append(_clip(img, start + sec, min(1.0, dur - sec), ctx.x0, ctx.y(0.105), fade=0, fade_out=0))
    return clips


def _frame_corners(ctx, start, dur):
    """Ecken-Rahmen wie im Kamerasucher (für CCTV)."""
    w, h = ctx.box_w, int(ctx.H * 0.44)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    L, c = 70, (235, 255, 235, 200)
    for (x, y, dx, dy) in ((0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)):
        d.line([(x, y), (x + dx * L, y)], fill=c, width=5)
        d.line([(x, y), (x, y + dy * L)], fill=c, width=5)
    return [_clip(img, start, dur, ctx.x0, ctx.y(0.10), fade=0, fade_out=0)]


def _highlight(ctx, scene, start, dur):
    """Auflösung bei der Überwachungskamera: rotes Kreisen um das veränderte Objekt."""
    from .scenes import cctv_object_pos

    pos = cctv_object_pos(ctx.story.setting, scene.change) if scene.change else None
    if not pos:
        return []
    r = 125
    img = Image.new("RGBA", (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([10, 10, r * 2 + 10, r * 2 + 10], outline=(255, 50, 60, 255), width=12)
    x, y = int(pos[0] * ctx.W) - r - 10, int(pos[1] * ctx.H) - r - 10
    return [_clip(img, start + 0.3, dur - 0.3, x, y, fade=0.25, fade_out=0)]


def hook_title(ctx, text, dur=2.6):
    if not text:
        return []
    size = 104
    f = _font(ctx.cfg, size)
    while size > 56 and max(f.getlength(w) for w in text.upper().split()) > ctx.box_w - 90:
        size -= 8                                   # längstes Wort muss in den sicheren Bereich passen
        f = _font(ctx.cfg, size)
    lines = _wrap(text.upper(), f, ctx.box_w - 70)
    lh = int(size * 1.14)
    w = int(max(f.getlength(l) for l in lines)) + 70
    img = Image.new("RGBA", (w, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, img.height - 1], radius=28, fill=ctx.accent + (238,))
    for i, l in enumerate(lines):
        d.text(((w - f.getlength(l)) / 2, 16 + i * lh), l, font=f, fill="white", stroke_width=7, stroke_fill=(0, 0, 0))
    x = int(ctx.W * (SAFE_X0 + SAFE_X1) / 2 - w / 2)
    y = ctx.y(0.30) if ctx.fmt in ("imposter",) else ctx.y(0.16)
    return [_clip(img, 0, dur, x, y, fade=0)]   # sofort sichtbar: erstes Bild = Vorschaubild auf TikTok


def episode_badge(ctx, dur=3.2):
    st = ctx.story
    if not st.episode:
        return []
    f = _font(ctx.cfg, 34)
    text = f"FOLGE {st.episode}" + (f" · {st.series_name[:26]}" if st.series_name else "")
    w = int(f.getlength(text)) + 44
    img = Image.new("RGBA", (w, 58), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 57], radius=29, fill=(255, 255, 255, 230))
    d.text((22, 9), text, font=f, fill=(12, 12, 16))
    return [_clip(img, 0, dur, ctx.x0, ctx.y(0.055), fade=0.2)]


# ------------------------------------------------------------------ Szene → Grafiken

def scene_overlays(ctx: OverlayContext, scene, index: int, start: float, dur: float) -> list:
    k, fmt = scene.kind, ctx.fmt
    clips = []
    if fmt == "cctv":
        clips += _cctv_hud(ctx, scene, index, start, dur) + _frame_corners(ctx, start, dur)
        if k == "reveal":
            clips += _highlight(ctx, scene, start, dur)
    if fmt in ("imposter", "krimi") and k in ("statement", "suspect", "clue", "evidence", "countdown", "reveal") \
            and (fmt == "imposter" or k in ("countdown", "reveal")):
        clips += _lineup(ctx, start, dur, speaker=scene.speaker, culprit_reveal=(k == "reveal"))
    under = 0.27 if fmt == "imposter" or (fmt == "krimi" and k in ("countdown", "reveal")) else 0.16
    if k in ("statement", "suspect"):
        clips += _speech(ctx, scene, start, dur, y=under if fmt == "imposter" else 0.14,
                         label="VERDÄCHTIG" if k == "suspect" else None)
    elif k == "clue":
        y = under if fmt != "cctv" else 0.22
        clips += _text_card(ctx, "HINWEIS", scene.on_screen or scene.text, start, dur, y, size=50)
    elif k == "evidence":
        label, _, text = (scene.on_screen or scene.text).partition(":")
        clips += _text_card(ctx, label.strip() if text else "BEWEIS", text.strip() or label, start, dur, 0.15,
                            size=50, paper=True, rotate=-2.5)
    elif k == "countdown":
        clips += _countdown(ctx, scene, start, dur)
    elif k == "choice":
        clips += _choices(ctx, scene, start, dur)
    elif k == "reveal":
        y = under if fmt != "cctv" else 0.22
        clips += _text_card(ctx, "AUFLÖSUNG", scene.on_screen or scene.text, start, dur, y + 0.005, size=58, center=True)
    elif k == "level":
        clips += _level_title(ctx, scene, start, dur)
    elif k == "rule":
        label, _, text = (scene.on_screen or scene.text).partition(":")
        clips += _text_card(ctx, label.strip().upper() if text else "REGEL", text.strip() or label, start, dur, 0.17,
                            size=52, paper=True, rotate=1.5)
    elif k in ("cliffhanger", "teaser"):
        y = 0.22 if fmt == "cctv" else 0.16
        clips += _text_card(ctx, "FORTSETZUNG FOLGT" if k == "cliffhanger" else "NÄCHSTE FOLGE",
                            scene.on_screen or ctx.story.next_teaser or scene.text, start, dur, y, size=50, center=True)
    elif k == "narration" and scene.on_screen and fmt != "cctv":
        clips += _text_card(ctx, None, scene.on_screen, start, dur, under if fmt == "imposter" else 0.16,
                            size=46, center=True)
    return clips
