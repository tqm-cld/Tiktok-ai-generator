"""Serien: Name, Folgen, wiederkehrende Figuren, feste Tatsachen und offene Cliffhanger.

Gespeichert als JSON in data/series/<id>.json (lokal, wird nicht auf GitHub hochgeladen).
Jede neue Folge bekommt den bisherigen Verlauf mit – vom Offline-Generator und von Claude.
"""

import json
import re
import secrets
import threading
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from .config import PROJECT_ROOT
from .formats import get_format

SERIES_DIR = PROJECT_ROOT / "data" / "series"
_lock = threading.Lock()


def _path(series_id: str, base: Path | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9-]{3,80}", series_id or ""):
        raise ValueError("Ungültige Serien-ID")
    return (base or SERIES_DIR) / f"{series_id}.json"


def create_series(name: str, fmt: str, idea: str = "", base: Path | None = None) -> dict:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("ä", "ae").replace("ö", "oe")
                  .replace("ü", "ue").replace("ß", "ss")).strip("-")[:40] or "serie"
    series = {"id": f"{slug}-{secrets.token_hex(3)}", "name": name.strip()[:80] or "Neue Serie",
              "format": get_format(fmt).key, "idea": idea.strip()[:300], "created": datetime.now().isoformat(timespec="seconds"),
              "characters": [], "facts": [], "open_threads": [], "episodes": [], "state": {}, "pending_choices": []}
    save_series(series, base)
    return series


def save_series(series: dict, base: Path | None = None) -> None:
    path = _path(series["id"], base)
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(series, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


def load_series(series_id: str, base: Path | None = None) -> dict:
    path = _path(series_id, base)
    if not path.exists():
        raise FileNotFoundError("Serie nicht gefunden")
    return json.loads(path.read_text(encoding="utf-8"))


def list_series(base: Path | None = None) -> list[dict]:
    folder = base or SERIES_DIR
    out = []
    for p in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if folder.exists() else []:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        last = s["episodes"][-1] if s.get("episodes") else {}
        out.append({"id": s["id"], "name": s["name"], "format": s["format"], "episodes": len(s.get("episodes", [])),
                    "next_episode": len(s.get("episodes", [])) + 1, "last_title": last.get("title", ""),
                    "next_teaser": last.get("next_teaser", ""), "open_threads": s.get("open_threads", []),
                    "pending_choices": s.get("pending_choices", [])})
    return out


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def check_consistency(series: dict | None, story) -> list[str]:
    """Findet Widersprüche zwischen der neuen Folge und dem bisherigen Serienverlauf."""
    if not series:
        return []
    problems = []
    known = {c["name"]: c.get("role", "") for c in series.get("characters", [])}
    for c in story.characters:
        if c.name in known and known[c.name] and c.role and c.role != known[c.name]:
            problems.append(f"Figur {c.name} hatte bisher die Rolle „{known[c.name]}“, jetzt „{c.role}“.")
    for e in series.get("episodes", []):
        if story.signature and e.get("signature"):        # Offline-Folgen: eindeutige Kennung vergleichen
            if e["signature"] == story.signature:
                problems.append(f"Diese Folge wiederholt Folge {e['episode']}.")
        elif story.summary and e.get("summary") and _similar(story.summary, e["summary"]) > 0.85:
            problems.append(f"Die Handlung ist fast gleich wie in Folge {e['episode']}.")
    for r in story.resolved_threads:
        if series.get("open_threads") and not any(_similar(r, o) > 0.4 for o in series["open_threads"]) \
                and not r.startswith("Entscheidung"):
            problems.append(f"Aufgelöster Cliffhanger „{r}“ war gar nicht offen.")
    return problems


def record_episode(series: dict, story, video_name: str = "", extra: dict | None = None,
                   base: Path | None = None) -> dict:
    """Speichert die fertige Folge und aktualisiert Figuren, Tatsachen und Cliffhanger."""
    number = len(series.get("episodes", [])) + 1
    series.setdefault("episodes", []).append({
        "episode": number, "title": story.title, "summary": story.summary, "culprit": story.culprit,
        "signature": story.signature, "open_threads": story.open_threads, "resolved_threads": story.resolved_threads,
        "choices": story.choices, "next_teaser": story.next_teaser, "video": video_name,
        "created": datetime.now().isoformat(timespec="seconds"), **(extra or {}),
    })
    known = {c["name"] for c in series.get("characters", [])}
    for c in story.characters:
        if c.name not in known:
            series.setdefault("characters", []).append(c.model_dump())
    for f in story.facts:
        if f not in series.setdefault("facts", []):
            series["facts"].append(f)
    still_open = [o for o in series.get("open_threads", [])
                  if not any(_similar(o, r) > 0.4 for r in story.resolved_threads)]
    series["open_threads"] = (still_open + [t for t in story.open_threads if t not in still_open])[-6:]
    series["pending_choices"] = story.choices
    series.setdefault("state", {}).update(getattr(story, "_state", {}) or {})
    save_series(series, base)
    return series
