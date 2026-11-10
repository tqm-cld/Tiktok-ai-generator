"""Ausgabenbuch: merkt sich, was jedes Video tatsächlich gekostet hat, und wacht über das Monatsbudget.

Gespeichert wird lokal in data/ausgaben.json (wird nicht auf GitHub hochgeladen).
Hinweis: Die Beträge werden aus den Verbrauchsangaben der Anbieter berechnet. Maßgeblich ist am
Ende immer die Abrechnung im Konto des Anbieters.
"""

import json
import threading
from datetime import datetime
from pathlib import Path

from .config import PROJECT_ROOT

LEDGER_FILE = PROJECT_ROOT / "data" / "ausgaben.json"
_lock = threading.Lock()


def _load(path: Path = LEDGER_FILE) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def record(kind: str, usd: float, note: str = "", path: Path = LEDGER_FILE) -> None:
    """Trägt eine Ausgabe ein, z. B. record("claude", 0.23, "Skript: Erde stoppt")."""
    if usd <= 0:
        return
    with _lock:
        entries = _load(path)
        entries.append({"time": datetime.now().isoformat(timespec="seconds"), "kind": kind,
                        "usd": round(usd, 4), "note": note})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def month_total(path: Path = LEDGER_FILE, now: datetime | None = None) -> float:
    month = (now or datetime.now()).strftime("%Y-%m")
    return round(sum(e["usd"] for e in _load(path) if e.get("time", "").startswith(month)), 4)


def summary(budget: float, path: Path = LEDGER_FILE) -> dict:
    spent = month_total(path)
    return {"spent": round(spent, 2), "budget": round(budget, 2), "remaining": round(max(0.0, budget - spent), 2)}
