"""Preiskatalog und Kostenschätzung pro Video.

WICHTIG: Die Preise stammen aus öffentlichen Übersichten (Stand November 2026) und
widersprechen sich teilweise. Vor der ersten Nutzung immer auf der Preisseite des
Anbieters prüfen! Alle Preise in US-Dollar (so rechnen die Anbieter ab).

Nur Einträge mit `integrated=True` können im Programm tatsächlich benutzt werden.
Kostenpflichtige Videomodelle werden erst nach deiner ausdrücklichen Freigabe eingebaut.
"""

from dataclasses import asdict, dataclass

PRICES_AS_OF = "November 2026"


@dataclass(frozen=True)
class VideoModel:
    key: str
    name: str
    provider: str
    usd_per_second: float      # Preis pro generierter Videosekunde (ohne Ton, wo möglich)
    clip_seconds: int          # typische Cliplänge pro Generierung
    resolution: str
    quality: int               # 1-5 Sterne (Bewegung, Realismus, Prompt-Treue) – grobe Einschätzung
    notes: str
    integrated: bool = False


VIDEO_MODELS: list[VideoModel] = [
    VideoModel("stock", "Testmodus: Stock-Clips + Kamerafahrten", "Pexels (kostenlos)",
               0.0, 0, "bis 1080p", 2,
               "Echte Hochkant-Stockvideos, per Schnitt und Zoom dynamisiert. Kostenlos, passt aber nicht "
               "immer exakt zum Thema.", integrated=True),
    VideoModel("ltx-fast", "LTX-2.3 Fast", "fal.ai", 0.05, 5, "1080p", 3,
               "Sehr günstig und schnell, sichtbar schwächer bei komplexen Szenen."),
    VideoModel("hailuo-fast", "MiniMax Hailuo 2.3 Fast", "MiniMax API", 0.19 / 6, 6, "768p", 3,
               "Offiziell $0.19 pro 6-s-Clip. Gute Bewegung fürs Geld, nur 768p. "
               "Als 'legacy' gelistet – Nachfolger H3 kostet $0.08/s."),
    VideoModel("veo-lite", "Google Veo 3.1 Lite", "Google (Vertex AI / Gemini API)", 0.03, 8, "720p", 4,
               "$0.03/s ohne Ton (Vertex), $0.05/s mit Ton (Gemini API). Bestes Preis-Leistungs-Verhältnis. "
               "Achtung: Gemini-API-Vorschau sollte laut einer Quelle im Okt. 2026 auslaufen – Verfügbarkeit prüfen."),
    VideoModel("kling-26", "Kling 2.6 Pro", "fal.ai", 0.07, 5, "1080p", 4,
               "Sehr flüssige Bewegungen, beliebt für 'Doku'-Optik."),
    VideoModel("veo-fast", "Google Veo 3.1 Fast", "Google (Gemini API)", 0.10, 8, "720p", 5,
               "$0.10/s (720p, mit Ton). Sehr realistisch, starke Physik."),
    VideoModel("wan-3", "Wan 3.0", "fal.ai", 0.10, 5, "720p", 4,
               "Open-Source-Modell, auch selbst hostbar (dann nur GPU-Kosten)."),
    VideoModel("kling-3", "Kling 3 Pro", "fal.ai", 0.112, 5, "1080p", 5,
               "Top-Qualität, Preise je nach Quelle $0.11-0.34/s (mit Ton teurer)."),
    VideoModel("seedance-2-fast", "Seedance 2.0 Fast", "fal.ai", 0.24, 5, "720p", 5,
               "Hervorragend, aber teuer (inkl. Ton). Direkt bei BytePlus ca. halber Preis."),
]

# Hinweis: Sora 2 fehlt absichtlich – die API wurde laut Berichten im September 2026 abgeschaltet.

CLAUDE_MODEL = "claude-opus-5-5"
CLAUDE_USD_PER_MTOK_IN = 4.00
CLAUDE_USD_PER_MTOK_OUT = 20.00
WEB_SEARCH_USD_PER_SEARCH = 0.01  # $10 pro 1000 Suchen

ELEVENLABS_USD_PER_1K_CHARS = 0.08  # Eleven v3 / Multilingual v2 nach Preissenkung Okt. 2026


def model_by_key(key: str) -> VideoModel:
    for m in VIDEO_MODELS:
        if m.key == key:
            return m
    raise KeyError(key)


def estimate_script_cost(fact_check: bool = True) -> tuple[float, float]:
    """Grobe Spanne (min, max) für Recherche + Skript mit Claude."""
    # Recherche: Suchergebnisse sind lang (viele Eingabe-Tokens)
    research_lo = (15_000 * CLAUDE_USD_PER_MTOK_IN + 1_500 * CLAUDE_USD_PER_MTOK_OUT) / 1e6 + 3 * WEB_SEARCH_USD_PER_SEARCH
    research_hi = (45_000 * CLAUDE_USD_PER_MTOK_IN + 5_000 * CLAUDE_USD_PER_MTOK_OUT) / 1e6 + 6 * WEB_SEARCH_USD_PER_SEARCH
    script_lo = (4_000 * CLAUDE_USD_PER_MTOK_IN + 2_000 * CLAUDE_USD_PER_MTOK_OUT) / 1e6
    script_hi = (8_000 * CLAUDE_USD_PER_MTOK_IN + 6_000 * CLAUDE_USD_PER_MTOK_OUT) / 1e6
    if not fact_check:
        return script_lo, script_hi
    return research_lo + script_lo, research_hi + script_hi


def estimate_video_cost(model_key: str, seconds: int, ai_share: float = 1.0) -> tuple[float, float]:
    """Kosten für die KI-Videoclips. `ai_share` = Anteil der Szenen, die per KI erzeugt werden.

    Es wird mit ganzen Clips gerechnet (man bezahlt immer den ganzen Clip), plus ca. 20 %
    Reserve für misslungene Clips, die neu erzeugt werden müssen."""
    m = model_by_key(model_key)
    if m.usd_per_second == 0:
        return 0.0, 0.0
    needed = seconds * ai_share
    clips = max(1, round(needed / m.clip_seconds + 0.49))
    base = clips * m.clip_seconds * m.usd_per_second
    return base, base * 1.2


def estimate(seconds: int, model_key: str = "stock", ai_share: float = 1.0,
             fact_check: bool = True, has_claude: bool = True, premium_voice: bool = False) -> dict:
    """Komplette Schätzung für ein Video – wird in der Weboberfläche angezeigt."""
    items = []
    if has_claude:
        lo, hi = estimate_script_cost(fact_check)
        items.append({"label": "Skript + Faktencheck (Claude, mit Websuche)" if fact_check else "Skript (Claude)",
                      "min": lo, "max": hi})
    else:
        items.append({"label": "Skript: Demo-Skript (kein Claude-Schlüssel)", "min": 0.0, "max": 0.0})

    if premium_voice:
        chars = seconds * 15  # ca. 15 Zeichen pro gesprochener Sekunde
        cost = chars / 1000 * ELEVENLABS_USD_PER_1K_CHARS
        items.append({"label": "KI-Stimme (ElevenLabs)", "min": cost, "max": cost * 1.1})
    else:
        items.append({"label": "KI-Stimme (Microsoft Edge, kostenlos)", "min": 0.0, "max": 0.0})

    m = model_by_key(model_key)
    lo, hi = estimate_video_cost(model_key, seconds, ai_share)
    items.append({"label": f"Videoszenen: {m.name}", "min": lo, "max": hi})
    items.append({"label": "Musik, Soundeffekte, Untertitel, Schnitt (lokal)", "min": 0.0, "max": 0.0})

    total_lo = sum(i["min"] for i in items)
    total_hi = sum(i["max"] for i in items)
    return {
        "items": items,
        "total_min": round(total_lo, 2),
        "total_max": round(total_hi, 2),
        "currency": "USD",
        "paid": total_hi > 0,
        "prices_as_of": PRICES_AS_OF,
    }


def catalog() -> list[dict]:
    """Alle Modelle mit Beispielkosten für ein 45-s-Video."""
    rows = []
    for m in VIDEO_MODELS:
        lo, hi = estimate_video_cost(m.key, 45)
        rows.append({**asdict(m), "cost_45s_min": round(lo, 2), "cost_45s_max": round(hi, 2)})
    return rows
