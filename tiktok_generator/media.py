"""Schritt 3: Passende Hintergrund-Videos oder -Bilder besorgen.

Reihenfolge:
  1. Hochkant-Video von Pexels (kostenlos, API-Schlüssel nötig)
  2. Hochkant-Foto von Pexels
  3. Ersatz: ein selbst erzeugter atmosphärischer Hintergrund (funktioniert immer, auch offline)
"""

import hashlib
import random
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter

from .config import Config

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"


def _download(url: str, target: Path) -> Path:
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(target, "wb") as f:
            for part in r.iter_content(chunk_size=1 << 16):
                f.write(part)
    return target


def _pexels_video(query: str, cfg: Config, target_dir: Path) -> Path | None:
    r = requests.get(
        PEXELS_VIDEO_URL,
        headers={"Authorization": cfg.pexels_api_key},
        params={"query": query, "orientation": "portrait", "per_page": 8},
        timeout=20,
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])
    random.shuffle(videos)
    for video in videos:
        # Datei suchen, die hochkant ist und nicht unnötig riesig (≤ 1920 Pixel hoch)
        files = [
            f for f in video.get("video_files", [])
            if f.get("height") and f.get("width")
            and f["height"] > f["width"] and f["height"] <= 1920
        ]
        if files:
            best = max(files, key=lambda f: f["height"])
            return _download(best["link"], target_dir / f"pexels_{video['id']}.mp4")
    return None


def _pexels_photo(query: str, cfg: Config, target_dir: Path) -> Path | None:
    r = requests.get(
        PEXELS_PHOTO_URL,
        headers={"Authorization": cfg.pexels_api_key},
        params={"query": query, "orientation": "portrait", "per_page": 8},
        timeout=20,
    )
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        return None
    photo = random.choice(photos)
    return _download(photo["src"]["large2x"], target_dir / f"pexels_{photo['id']}.jpg")


def _gradient_image(query: str, cfg: Config, target_dir: Path) -> Path:
    """Erzeugt einen atmosphärischen Hintergrund (Nebel-/Wolkenlicht mit Sternen).
    Farbe und Muster hängen vom Suchbegriff ab – so sieht jede Szene anders aus."""
    seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    w, h = int(cfg.width * 1.2), int(cfg.height * 1.2)   # etwas größer für die Kamerafahrten

    hue = rng.random()
    def color(light):
        import colorsys
        r, g, b = colorsys.hsv_to_rgb((hue + rng.uniform(-0.08, 0.08)) % 1, rng.uniform(0.5, 0.9), light)
        return int(r * 255), int(g * 255), int(b * 255)

    # grobes Zufallsraster → weich hochskaliert = Nebel
    small = Image.new("RGB", (6, 10))
    for x in range(6):
        for y in range(10):
            small.putpixel((x, y), color(rng.uniform(0.05, 0.55)))
    img = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(60))

    draw = ImageDraw.Draw(img)
    for _ in range(260):                                   # Sterne/Staubpartikel
        x, y, r = rng.randint(0, w), rng.randint(0, h), rng.choice([1, 1, 2, 2, 3])
        v = rng.randint(150, 255)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, v))

    # Vignette: Ränder abdunkeln
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse([-w * 0.2, -h * 0.1, w * 1.2, h * 1.1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(img, Image.new("RGB", (w, h), (0, 0, 0)), mask)

    path = target_dir / f"generated_{seed}.jpg"
    img.save(path, quality=92)
    return path


def fetch_media(query: str, cfg: Config, target_dir: Path) -> Path:
    """Gibt den Pfad zu einem Video (.mp4) oder Bild (.jpg/.png) zurück."""
    target_dir.mkdir(parents=True, exist_ok=True)
    if cfg.pexels_api_key:
        for finder in (_pexels_video, _pexels_photo):
            try:
                found = finder(query, cfg, target_dir)
                if found:
                    return found
            except requests.RequestException as e:
                print(f"  ⚠ Pexels-Fehler bei '{query}': {e}")
    return _gradient_image(query, cfg, target_dir)


def is_video(path: Path) -> bool:
    return path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}
