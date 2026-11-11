"""Kostenlose, lokal gezeichnete Kulissen für die Formate (keine KI, kein Internet nötig).

Jeder Bildstil ("look") malt eine stimmige Szene im Hochformat – etwas größer als 1080×1920,
damit Kamerafahrten (Zoom/Schwenk) Platz haben:
  - cctv:      Flur/Raum aus Sicht einer Überwachungskamera – mit veränderbaren Objekten
               (Tür, Stuhl, Schatten, Lampe, Uhr) für „Bemerkst du die Veränderung?“
  - corridor:  endlose, menschenleere Orte (Flur, Schwimmbad, Parkhaus) für „Das unendliche Level“
  - lineup:    Innenraum je Schauplatz (Raumstation, Zug, Schiff, Forschungsstation) für „Imposter“
  - board:     Ermittlungswand mit Zetteln und roten Fäden für „Kriminalfall“
  - landscape: Wüste, Schneesturm, Insel für „Du entscheidest“
Gleiche Eingaben ergeben immer dasselbe Bild (Zwischenspeicher), damit Szenen zusammenpassen.
"""

import hashlib
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SCALE = 1.2  # Reserve für Kamerafahrten


def _canvas(cfg):
    return int(cfg.width * SCALE), int(cfg.height * SCALE)


def _vgrad(w, h, top, bottom):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def _vignette(img, strength=0.65):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([-w * 0.25, -h * 0.12, w * 1.25, h * 1.12], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) // 6))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, Image.blend(dark, img, 1 - strength), mask)


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ------------------------------------------------------------------ Perspektivischer Raum

def _corridor(w, h, pal, vp=(0.5, 0.42), depth=0.16, doors=4, lights=5, rng=None, back="door"):
    """Zeichnet einen Gang mit Fluchtpunkt. Gibt Bild + wichtige Koordinaten zurück."""
    rng = rng or random.Random(1)
    img = Image.new("RGB", (w, h), pal["ceiling"])
    d = ImageDraw.Draw(img)
    vx, vy = w * vp[0], h * vp[1]
    bw, bh = w * depth, h * depth * 1.25                    # hintere Wand
    bx0, by0, bx1, by1 = vx - bw, vy - bh, vx + bw, vy + bh * 0.9
    d.polygon([(0, h), (w, h), (bx1, by1), (bx0, by1)], fill=pal["floor"])
    d.polygon([(0, 0), (bx0, by0), (bx0, by1), (0, h)], fill=pal["wall_l"])
    d.polygon([(w, 0), (bx1, by0), (bx1, by1), (w, h)], fill=pal["wall_r"])
    d.polygon([(0, 0), (w, 0), (bx1, by0), (bx0, by0)], fill=pal["ceiling"])
    d.rectangle([bx0, by0, bx1, by1], fill=pal["back"])
    # Bodenfugen für Tiefe
    for i in range(1, 9):
        t = (i / 9) ** 1.8
        y = by1 + (h - by1) * t
        x0 = bx0 + (0 - bx0) * t
        x1 = bx1 + (w - bx1) * t
        d.line([(x0, y), (x1, y)], fill=_shade(pal["floor"], 0.85), width=max(1, int(3 * t)))
    # Deckenlampen
    for i in range(lights):
        t = ((i + 0.6) / lights) ** 1.6
        y = by0 * (1 - t) + 0 * t
        y = by0 - (by0 - h * 0.02) * t
        lw = bw * (1 + t * 4.2) * 0.35
        cx = vx
        d.rounded_rectangle([cx - lw, y - 4 - 10 * t, cx + lw, y + 4 + 10 * t], radius=6, fill=pal["light"])
    # Seitentüren
    for side in (-1, 1):
        for i in range(doors):
            t0 = ((i + 0.2) / doors) ** 1.5
            t1 = ((i + 0.55) / doors) ** 1.5
            def wall_pt(t, yfrac):
                x_back = bx0 if side < 0 else bx1
                x_front = 0 if side < 0 else w
                x = x_back + (x_front - x_back) * t
                top = by0 + (0 - by0) * t
                bot = by1 + (h - by1) * t
                return x, top + (bot - top) * yfrac
            p = [wall_pt(t0, 0.32), wall_pt(t1, 0.28), wall_pt(t1, 1.0), wall_pt(t0, 1.0)]
            d.polygon(p, fill=pal["door"], outline=_shade(pal["door"], 0.7))
    # hintere Tür
    door = (vx - bw * 0.32, by0 + bh * 0.45, vx + bw * 0.32, by1)
    if back == "door":
        d.rectangle(door, fill=pal["door"], outline=_shade(pal["door"], 0.6), width=3)
    return img, {"vp": (vx, vy), "back": (bx0, by0, bx1, by1), "door": door}


PALETTES = {
    "hotel": dict(floor=(92, 54, 48), wall_l=(150, 132, 104), wall_r=(138, 120, 95), ceiling=(170, 160, 140),
                  back=(120, 105, 85), door=(96, 68, 48), light=(255, 244, 210)),
    "garage": dict(floor=(70, 72, 74), wall_l=(112, 114, 116), wall_r=(100, 102, 104), ceiling=(88, 90, 92),
                   back=(60, 62, 64), door=(160, 150, 60), light=(230, 240, 255)),
    "museum": dict(floor=(110, 92, 70), wall_l=(170, 160, 150), wall_r=(158, 148, 138), ceiling=(190, 184, 176),
                   back=(140, 130, 120), door=(80, 64, 50), light=(255, 248, 230)),
    "warehouse": dict(floor=(84, 80, 72), wall_l=(120, 112, 98), wall_r=(108, 100, 88), ceiling=(70, 68, 64),
                      back=(60, 58, 54), door=(90, 110, 130), light=(240, 245, 255)),
    "school": dict(floor=(120, 108, 92), wall_l=(176, 186, 170), wall_r=(164, 174, 158), ceiling=(200, 200, 190),
                   back=(150, 160, 145), door=(110, 82, 60), light=(255, 255, 235)),
    "office": dict(floor=(96, 96, 104), wall_l=(184, 184, 178), wall_r=(170, 170, 165), ceiling=(206, 206, 200),
                   back=(150, 150, 146), door=(120, 120, 128), light=(250, 252, 255)),
    "liminal": dict(floor=(150, 128, 70), wall_l=(214, 196, 120), wall_r=(200, 182, 108), ceiling=(222, 210, 150),
                    back=(186, 168, 96), door=(170, 150, 90), light=(255, 252, 210)),
    "pool": dict(floor=(120, 190, 200), wall_l=(200, 226, 228), wall_r=(186, 214, 216), ceiling=(214, 222, 214),
                 back=(160, 206, 212), door=(150, 190, 196), light=(255, 255, 236)),
    "space": dict(floor=(40, 52, 66), wall_l=(70, 88, 108), wall_r=(60, 78, 98), ceiling=(50, 64, 80),
                  back=(24, 30, 44), door=(90, 110, 130), light=(160, 230, 255)),
    "polar": dict(floor=(150, 156, 160), wall_l=(208, 214, 220), wall_r=(196, 202, 208), ceiling=(220, 226, 232),
                  back=(120, 140, 160), door=(200, 90, 60), light=(240, 250, 255)),
    "train": dict(floor=(82, 50, 36), wall_l=(150, 98, 64), wall_r=(140, 90, 58), ceiling=(176, 150, 120),
                  back=(30, 38, 60), door=(110, 70, 44), light=(255, 228, 170)),
    "ship": dict(floor=(70, 60, 54), wall_l=(210, 206, 196), wall_r=(196, 192, 182), ceiling=(226, 222, 212),
                 back=(40, 60, 90), door=(60, 70, 90), light=(255, 246, 220)),
}


# Lage der veränderbaren Objekte (Anteil von Breite/Höhe). Die feste Überwachungskamera zeigt das
# ganze Bild, daher gelten dieselben Anteile im fertigen Video (für den Markierungskreis der Auflösung).
CCTV_POS = {"chair": (0.40, 0.555), "clock": (0.82, 0.30), "shadow": (0.78, 0.43)}


def cctv_vp_x(setting: str) -> float:
    seed = int(hashlib.md5(setting.encode()).hexdigest()[:4], 16)
    return 0.5 + (seed % 3 - 1) * 0.06


def cctv_object_pos(setting: str, change: str):
    """Wo im Bild sich das veränderte Objekt befindet (Anteile), für den Markierungskreis."""
    if change == "door":
        return cctv_vp_x(setting) + 0.03, 0.39
    if change == "light":
        return cctv_vp_x(setting), 0.19
    return CCTV_POS.get(change)


def _cctv_room(cfg, location_seed: int, change: str, rng):
    w, h = _canvas(cfg)
    pal_key = ["hotel", "garage", "museum", "warehouse", "school", "office"][location_seed % 6]
    pal = PALETTES[pal_key]
    img, geo = _corridor(w, h, pal, vp=(0.5 + (location_seed % 3 - 1) * 0.06, 0.36), depth=0.15,
                         doors=3, lights=4, rng=rng, back="door")
    d = ImageDraw.Draw(img, "RGBA")
    bx0, by0, bx1, by1 = geo["back"]
    door = geo["door"]
    if change == "door":   # Tür einen Spalt offen: dunkler Spalt + Lichtkeil auf dem Boden
        gap = (door[2] - door[0]) * 0.40
        d.rectangle([door[2] - gap, door[1], door[2], door[3]], fill=(12, 12, 14))
        d.polygon([(door[2] - gap, door[3]), (door[2], door[3]), (door[2] + gap * 3, h * 0.62),
                   (door[2] - gap * 0.5, h * 0.62)], fill=(255, 240, 200, 40))
    # Stuhl: steht an der linken Wand – oder (Veränderung) mitten im Raum. Hell, damit er auch im
    # Schwarzweiß-Kamerabild klar zu erkennen ist.
    cx, cy, cs = (w * 0.22, h * 0.66, 1.25) if change != "chair" else (w * CCTV_POS["chair"][0], h * CCTV_POS["chair"][1], 1.0)
    s = 80 * cs
    chair = (226, 222, 210)
    d.rectangle([cx - s, cy - s * 0.2, cx + s, cy + s * 0.15], fill=chair)                # Sitz
    d.rectangle([cx - s, cy - s * 2.0, cx - s * 0.75, cy], fill=chair)                     # Lehne
    for lx in (cx - s, cx + s * 0.8):
        d.rectangle([lx, cy, lx + s * 0.18, cy + s * 1.3], fill=chair)
    # Uhr an der rechten Wand
    ux, uy, ur = w * CCTV_POS["clock"][0], h * CCTV_POS["clock"][1], 58
    d.ellipse([ux - ur, uy - ur, ux + ur, uy + ur], fill=(240, 240, 236), outline=(40, 40, 40), width=5)
    minute = 47 if change == "clock" else 0
    for ang, ln, wd in ((math.radians(minute * 6 - 90), ur * 0.8, 4), (math.radians(90 + 15), ur * 0.55, 6)):
        d.line([(ux, uy), (ux + math.cos(ang) * ln, uy + math.sin(ang) * ln)], fill=(20, 20, 20), width=wd)
    # Lampe hinten: an oder (Veränderung) aus
    lamp = ((bx0 + bx1) / 2, by0 + 18)
    if change == "light":
        d.rectangle([bx0, by0, bx1, by1], fill=(0, 0, 0, 120))
    else:
        d.ellipse([lamp[0] - 26, lamp[1] - 10, lamp[0] + 26, lamp[1] + 10], fill=(255, 250, 220))
    if change == "shadow":  # zweiter Schatten an der rechten Wand – ohne Person
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sx, sy = w * CCTV_POS["shadow"][0], h * CCTV_POS["shadow"][1]
        sd.ellipse([sx - 40, sy - 230, sx + 40, sy - 150], fill=(0, 0, 0, 150))
        sd.rounded_rectangle([sx - 75, sy - 150, sx + 75, sy + 140], radius=40, fill=(0, 0, 0, 150))
        img.paste(sh.filter(ImageFilter.GaussianBlur(14)), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    return _vignette(img, 0.55)


def _liminal(cfg, room_key: str, rng, variant: int = 0):
    w, h = _canvas(cfg)
    key = room_key.lower()
    if "schwimm" in key:
        pal = PALETTES["pool"]
    elif "park" in key or "bahnhof" in key:
        pal = PALETTES["garage"]
    else:
        pal = PALETTES["liminal"]
    vp_x = [0.5, 0.36, 0.64][variant % 3]                  # Gang biegt mal links, mal rechts ab
    img, geo = _corridor(w, h, pal, vp=(vp_x, 0.42), depth=0.07 + 0.02 * (variant % 2), doors=7, lights=8, rng=rng)
    d = ImageDraw.Draw(img, "RGBA")
    if "schwimm" in key:  # Wasserfläche
        d.polygon([(w * 0.18, h), (w * 0.82, h), (w * 0.54, h * 0.5), (w * 0.46, h * 0.5)], fill=(40, 150, 190, 170))
    # leichter Dunst
    haze = Image.new("RGBA", (w, h), (255, 245, 200, 0))
    ImageDraw.Draw(haze).ellipse([w * 0.3, h * 0.25, w * 0.7, h * 0.6], fill=(255, 245, 200, 70))
    img.paste(haze.filter(ImageFilter.GaussianBlur(80)), (0, 0), haze.filter(ImageFilter.GaussianBlur(80)))
    return _vignette(img, 0.5)


def _interior(cfg, setting: str, rng):
    w, h = _canvas(cfg)
    s = setting.lower()
    key = "space" if "raum" in s or "station aurora" in s else "polar" if "polar" in s or "forschung" in s \
        else "train" if "zug" in s else "ship" if "schiff" in s else "office"
    pal = PALETTES[key]
    img, geo = _corridor(w, h, pal, vp=(0.5, 0.40), depth=0.12, doors=3, lights=5, rng=rng, back="window")
    d = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = geo["back"]
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    r = (bx1 - bx0) * 0.38
    if key == "space":       # rundes Fenster mit Sternen
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(4, 6, 16), outline=(120, 140, 160), width=8)
        for _ in range(60):
            a, rr = rng.uniform(0, 6.28), rng.uniform(0, r * 0.9)
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 255))
    elif key in ("train", "ship"):  # Nachtfenster
        for i in (-1, 0, 1):
            d.rounded_rectangle([cx + i * r * 0.8 - r * 0.3, cy - r * 0.4, cx + i * r * 0.8 + r * 0.3, cy + r * 0.4],
                                radius=14 if key == "train" else 60, fill=(16, 24, 48), outline=(200, 190, 170), width=5)
    else:
        d.rectangle([cx - r, cy - r * 0.5, cx + r, cy + r * 0.5], fill=(200, 220, 240), outline=(90, 100, 110), width=6)
    return _vignette(img, 0.6)


def _board(cfg, rng):
    w, h = _canvas(cfg)
    img = _vgrad(w, h, (40, 30, 24), (20, 14, 10))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = w * 0.06, h * 0.08, w * 0.94, h * 0.82
    cork = Image.effect_noise((int(x1 - x0), int(y1 - y0)), 40).convert("RGB")
    cork = Image.blend(Image.new("RGB", cork.size, (150, 110, 70)), cork, 0.18)
    img.paste(cork, (int(x0), int(y0)))
    d.rectangle([x0, y0, x1, y1], outline=(70, 46, 28), width=18)
    pins = []
    for _ in range(9):
        pw, ph = rng.randint(150, 260), rng.randint(110, 200)
        px, py = rng.uniform(x0 + 40, x1 - pw - 40), rng.uniform(y0 + 40, y1 - ph - 40)
        paper = Image.new("RGBA", (pw, ph), rng.choice([(240, 236, 220, 255), (250, 246, 200, 255), (230, 230, 230, 255)]))
        pd = ImageDraw.Draw(paper)
        for ly in range(20, ph - 10, 22):
            pd.line([(14, ly), (pw - rng.randint(20, 70), ly)], fill=(120, 120, 120, 255), width=3)
        paper = paper.rotate(rng.uniform(-8, 8), expand=True, resample=Image.BICUBIC)
        img.paste(paper, (int(px), int(py)), paper)
        pins.append((px + pw / 2, py + 14))
    for a, b in zip(pins, pins[1:]):
        if rng.random() < 0.7:
            d.line([a, b], fill=(200, 30, 30), width=5)
    for p in pins:
        d.ellipse([p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10], fill=(210, 30, 30))
    light = Image.new("L", (w, h), 0)
    ImageDraw.Draw(light).ellipse([w * 0.1, h * 0.05, w * 0.9, h * 0.65], fill=255)
    light = light.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(img, Image.blend(Image.new("RGB", (w, h)), img, 0.45), light)
    return img


def _prop(d, kind, x, y, scale, col):
    """Einfache Silhouetten als Requisiten (Jeep, Zelt, Wrack, Person)."""
    s = scale
    if kind == "jeep":
        d.rounded_rectangle([x - 150 * s, y - 70 * s, x + 150 * s, y], radius=int(18 * s), fill=col)
        d.polygon([(x - 90 * s, y - 70 * s), (x - 60 * s, y - 130 * s), (x + 70 * s, y - 130 * s), (x + 100 * s, y - 70 * s)], fill=col)
        for wx in (x - 95 * s, x + 95 * s):
            d.ellipse([wx - 38 * s, y - 30 * s, wx + 38 * s, y + 46 * s], fill=_shade(col, 0.6))
    elif kind == "tent":
        d.polygon([(x - 140 * s, y), (x, y - 160 * s), (x + 140 * s, y)], fill=col)
        d.polygon([(x - 30 * s, y), (x, y - 70 * s), (x + 30 * s, y)], fill=_shade(col, 0.4))
    elif kind == "wreck":
        d.polygon([(x - 200 * s, y - 40 * s), (x + 160 * s, y - 70 * s), (x + 120 * s, y + 20 * s), (x - 170 * s, y + 30 * s)], fill=col)
        d.line([(x - 20 * s, y - 50 * s), (x + 30 * s, y - 260 * s)], fill=col, width=int(14 * s))
    else:  # person
        d.ellipse([x - 22 * s, y - 190 * s, x + 22 * s, y - 146 * s], fill=col)
        d.rounded_rectangle([x - 34 * s, y - 146 * s, x + 34 * s, y - 50 * s], radius=int(16 * s), fill=col)
        d.line([(x - 16 * s, y - 52 * s), (x - 24 * s, y)], fill=col, width=int(16 * s))
        d.line([(x + 16 * s, y - 52 * s), (x + 24 * s, y)], fill=col, width=int(16 * s))


def _footprints(d, w, h, rng, col):
    x, y = w * rng.uniform(0.35, 0.6), h * 0.98
    for i in range(14):
        side = -1 if i % 2 else 1
        r = 26 - i * 1.3
        d.ellipse([x + side * 30 - r, y - r * 1.5, x + side * 30 + r, y + r * 1.5], fill=col)
        y -= 95 - i * 4
        x += rng.uniform(-25, 25)


def _landscape(cfg, query: str, rng, night=False, variant: int = 0):
    """Drei Bildausschnitte je Landschaft: 0 = Weitwinkel, 1 = tiefer Horizont mit Requisite,
    2 = Nahaufnahme des Bodens mit Spuren. So wechselt das Bild alle paar Sekunden sichtbar."""
    w, h = _canvas(cfg)
    q = query.lower()
    v = variant % 3
    horizon = [0.52, 0.66, 0.34][v]
    if "snow" in q or "schnee" in q or "mountain" in q:
        img = _vgrad(w, h, (40, 52, 74), (150, 160, 176))
        d = ImageDraw.Draw(img)
        for i, col in enumerate([(120, 132, 150), (180, 190, 204), (230, 236, 244)]):
            base = h * (horizon - 0.07 + i * 0.12)
            pts = [(0, h)]
            x = 0
            while x <= w:
                pts.append((x, base - rng.uniform(80, 360) * (1 - i * 0.25) * (0.5 if v == 2 else 1)))
                x += rng.uniform(140, 300)
            pts += [(w, base), (w, h)]
            d.polygon(pts, fill=col)
        if v == 1:
            _prop(d, "tent", w * rng.uniform(0.3, 0.6), h * 0.80, 1.4, (200, 90, 50))
        if v == 2:
            _footprints(d, w, h, rng, (200, 208, 222))
        for _ in range(500):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.choice([2, 3, 4])
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))
        return _vignette(img.filter(ImageFilter.GaussianBlur(1)), 0.5)
    if "island" in q or "beach" in q or "insel" in q:
        img = _vgrad(w, h, (90, 160, 220), (190, 225, 245))
        d = ImageDraw.Draw(img)
        d.ellipse([w * 0.66, h * 0.08, w * 0.82, h * 0.17], fill=(255, 250, 220))
        sea0 = h * (horizon - 0.02)
        d.rectangle([0, sea0, w, sea0 + h * 0.16], fill=(30, 110, 160))
        for i in range(12):
            y = sea0 + 20 + i * 18
            d.line([(rng.uniform(0, w * 0.4), y), (rng.uniform(w * 0.6, w), y)], fill=(90, 170, 210), width=3)
        d.polygon([(0, sea0 + h * 0.14), (w, sea0 + h * 0.10), (w, h), (0, h)], fill=(226, 204, 150))
        if v == 1:
            _prop(d, "wreck", w * 0.58, sea0 + h * 0.20, 1.5, (90, 64, 44))
        if v == 2:
            _footprints(d, w, h, rng, (196, 172, 120))
        else:
            tx, ty = w * 0.22, sea0 + h * 0.14
            d.line([(tx, ty), (tx + 60, ty - h * 0.28)], fill=(70, 50, 30), width=22)
            for a in range(200, 340, 28):
                ang = math.radians(a)
                d.line([(tx + 60, ty - h * 0.28), (tx + 60 + math.cos(ang) * 210, ty - h * 0.28 + math.sin(ang) * -70 + 60)],
                       fill=(30, 90, 40), width=30)
        return _vignette(img, 0.4)
    # Wüste (Standard)
    top, bottom = ((24, 22, 50), (120, 70, 60)) if night else ((240, 170, 90), (250, 220, 160))
    img = _vgrad(w, h, top, bottom)
    d = ImageDraw.Draw(img)
    sun = [(0.6, 0.10, 0.18), (0.18, 0.18, 0.30), (0.55, 0.05, 0.12)][v]
    d.ellipse([w * sun[0], h * sun[1], w * (sun[0] + sun[2]), h * sun[1] + w * sun[2]],
              fill=(255, 240, 200) if not night else (230, 230, 250))
    for i, col in enumerate([(214, 150, 90), (200, 132, 72), (178, 110, 56)]):
        base = h * (horizon + i * 0.1)
        amp = 60 if v != 2 else 25
        pts = [(0, h)] + [(x, base + math.sin(x / (260 + i * 90) + i * 2 + v) * amp) for x in range(0, w + 40, 40)] + [(w, h)]
        d.polygon(pts, fill=_shade(col, 0.55) if night else col)
    if v == 1:
        _prop(d, "jeep", w * 0.62, h * 0.86, 1.3, (60, 46, 34))
    if v == 2:
        _footprints(d, w, h, rng, (150, 92, 44))
        for _ in range(40):  # Steine
            x, y, r = rng.uniform(0, w), rng.uniform(h * 0.5, h), rng.uniform(6, 22)
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(140, 90, 50))
    return _vignette(img, 0.45)


def render_scene_image(look: str, cfg, target_dir: Path, *, key: str = "", query: str = "", setting: str = "",
                       change: str = "", night: bool = False, variant: int = 0) -> Path:
    """Malt die Kulisse und speichert sie (gleiche Parameter → gleiche Datei).
    `variant` wechselt den Bildausschnitt von Szene zu Szene (Landschaft, Gang)."""
    sig = hashlib.md5(f"{look}|{key}|{query}|{setting}|{change}|{night}|{variant}".encode()).hexdigest()[:16]
    path = target_dir / f"scene_{look}_{sig}.jpg"
    if path.exists():
        return path
    target_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(int(sig[:8], 16))
    if look == "cctv":
        img = _cctv_room(cfg, int(hashlib.md5(setting.encode()).hexdigest()[:4], 16), change, rng)
    elif look == "corridor":
        img = _liminal(cfg, setting or key, rng, variant)
    elif look == "lineup":
        img = _interior(cfg, setting, rng)
    elif look == "board":
        img = _board(cfg, rng)
    else:
        img = _landscape(cfg, query or setting, rng, night=night, variant=variant)
    img.save(path, quality=92)
    return path
