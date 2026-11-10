"""Schritt 3: Passende Hintergrund-Videos oder -Bilder besorgen.

Reihenfolge:
  1. Hochkant-Video von Pexels (kostenlos, API-Schlüssel nötig)
  2. Hochkant-Foto von Pexels
  3. Ersatz: ein selbst erzeugter Farbverlauf (funktioniert immer, auch offline)
"""

import hashlib
import random
from pathlib import Path

import requests
from PIL import Image, ImageDraw

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
    """Erzeugt einen dunklen Farbverlauf. Die Farbe hängt vom Suchbegriff ab."""
    seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    top = tuple(rng.randint(20, 120) for _ in range(3))
    bottom = tuple(rng.randint(0, 40) for _ in range(3))

    w, h = cfg.width, cfg.height
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    # ein paar weiche Kreise, damit der Zoom-Effekt sichtbar ist
    for _ in range(6):
        x, y, r = rng.randint(0, w), rng.randint(0, h), rng.randint(80, 300)
        c = tuple(min(255, v + 40) for v in top)
        draw.ellipse([x - r, y - r, x + r, y + r], outline=c, width=6)

    path = target_dir / f"gradient_{seed}.png"
    img.save(path)
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
