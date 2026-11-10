"""Preiskatalog und Kostenschätzung pro Video.

WICHTIG: Die Preise stammen aus öffentlichen Übersichten (Stand November 2026) und
widersprechen sich teilweise. Vor der Freischaltung eines Modells prüfen wir den Preis auf der
offiziellen Seite des Anbieters. Alle Preise in US-Dollar (so rechnen die Anbieter ab).

Kostenpflichtige Videomodelle sind nur aufgelistet. Eingebaut werden sie ERST nach deiner Zustimmung.
"""

import math
from dataclasses import asdict, dataclass, field

PRICES_AS_OF = "November 2026"

# Hybrid-Modus: so viele Sekunden KI-Video plant der Kostenrechner pro "KI-Moment"
SECONDS_PER_AI_MOMENT = 4
RETRY_RESERVE = 0.20          # 20 % Reserve für misslungene Clips, die neu erzeugt werden


@dataclass(frozen=True)
class VideoModel:
    key: str
    name: str
    provider: str
    usd_per_second: float        # Preis pro bezahlter Videosekunde (ohne Ton, wo möglich)
    durations: tuple = ()        # erlaubte Cliplängen in s; leer = frei wählbar (sekundengenau)
    min_seconds: int = 1         # bei frei wählbarer Länge: Mindestlänge
    resolution: str = "720p"
    quality: int = 3             # 1-5 Sterne – grobe Einschätzung aus Testberichten, nicht selbst gemessen
    portrait: str = "ja"         # 9:16-Unterstützung
    setup: str = "einfach"       # Aufwand für die Kontoeinrichtung
    tier: str = "hybrid"         # "hybrid" = Kandidat für KI-Momente, "premium" = nur zum Vergleich
    notes: str = ""
    integrated: bool = False

    def billed_seconds(self, wanted: float) -> int:
        """Wie viele Sekunden man für einen Clip von `wanted` Sekunden bezahlen muss."""
        if self.durations:
            fitting = [d for d in self.durations if d >= wanted]
            return min(fitting) if fitting else max(self.durations)
        return max(self.min_seconds, math.ceil(wanted))

    def clip_cost(self, wanted: float) -> float:
        return self.billed_seconds(wanted) * self.usd_per_second


VIDEO_MODELS: list[VideoModel] = [
    VideoModel("stock", "Nur Stockvideos (Testmodus)", "Pexels", 0.0, resolution="bis 1080p", quality=2,
               tier="free", notes="Echte Hochkant-Videos, per Schnitt dynamisiert. Passt nicht immer exakt.",
               integrated=True),
    VideoModel("preview", "Hybrid-Vorschau (kostenlos)", "lokal", 0.0, resolution="bis 1080p", quality=2,
               tier="free", notes="Zeigt, welche Shots später KI-Szenen würden (markiert), nutzt aber noch Stockvideos.",
               integrated=True),

    # --- Kandidaten für den Hybrid-Modus (günstig, kurze Clips) ---
    VideoModel("seedance-15", "Seedance 1.5 Pro", "BytePlus (ByteDance)", 0.026, min_seconds=4, quality=4,
               portrait="ja", setup="mittel",
               notes="Token-Abrechnung ($1.20 pro 1 Mio. Tokens ohne Ton). 720p-Hochformat ≈ $0.026/s "
                     "(eigene Umrechnung). Sehr gutes Preis-Leistungs-Verhältnis."),
    VideoModel("grok-lite", "Grok Imagine Video 1.5 Lite", "xAI", 0.03, min_seconds=1, quality=3,
               portrait="zu prüfen", setup="einfach",
               notes="Sekundengenau 1–15 s, Text- oder Bild-zu-Video. Angaben je nach Quelle $0.02–0.03/s (720p)."),
    VideoModel("wan26-flash", "Wan 2.6 Flash (Bild→Video)", "Alibaba Cloud (Singapur)", 0.025, durations=(5, 10),
               quality=3, portrait="über Startbild", setup="aufwendig",
               notes="Günstigster Sekundenpreis (720p ohne Ton), braucht aber ein Startbild (z. B. Pexels-Foto). "
                     "Kein Gratis-Kontingent. Cliplängen bitte vor Integration prüfen."),
    VideoModel("veo-lite-vertex", "Google Veo 3.1 Lite (Vertex AI)", "Google Cloud", 0.03, durations=(4, 6, 8),
               quality=4, portrait="ja", setup="aufwendig",
               notes="Ohne Ton $0.03/s. Braucht ein Google-Cloud-Projekt mit Abrechnung (für Anfänger umständlicher)."),
    VideoModel("veo-lite", "Google Veo 3.1 Lite (Gemini API)", "Google AI Studio", 0.05, durations=(4, 6, 8),
               quality=4, portrait="ja", setup="einfach",
               notes="Einfacher API-Schlüssel, aber nur mit Ton abrechenbar ($0.05/s). Verfügbarkeit der "
                     "Vorschau prüfen (laut einer Quelle Ablauf Okt. 2026)."),
    VideoModel("hailuo-fast", "MiniMax Hailuo 2.3 Fast", "MiniMax", 0.19 / 6, durations=(6, 10), resolution="768p",
               quality=3, portrait="über Startbild", setup="mittel",
               notes="$0.19 pro 6-s-Clip – bei 4-s-Momenten zahlt man 2 s umsonst. Als 'legacy' gelistet."),

    # --- Premium (nur zum Vergleich) ---
    VideoModel("kling-26", "Kling 2.6 Pro", "fal.ai", 0.07, durations=(5, 10), resolution="1080p", quality=4,
               tier="premium", notes="Sehr flüssige Bewegungen."),
    VideoModel("veo-fast", "Google Veo 3.1 Fast", "Google AI Studio", 0.10, durations=(4, 6, 8), quality=5,
               tier="premium", notes="Sehr realistisch, starke Physik."),
    VideoModel("kling-3", "Kling 3 Pro", "fal.ai", 0.112, durations=(5, 10), resolution="1080p", quality=5,
               tier="premium", notes="Top-Qualität."),
]

# Claude-Modelle für Recherche & Skript: (Name, $ pro 1 Mio. Eingabe-Tokens, $ pro 1 Mio. Ausgabe-Tokens)
CLAUDE_MODELS = {
    "claude-opus-5-5": ("Claude Opus 5.5 – beste Recherche (Standard)", 4.00, 20.00),
    "claude-sonnet-5-5": ("Claude Sonnet 5.5 – halb so teuer", 2.00, 10.00),
    "claude-haiku-5-5": ("Claude Haiku 5.5 – am günstigsten, schwächerer Faktencheck", 0.10, 0.50),
}
DEFAULT_CLAUDE_MODEL = "claude-opus-5-5"
WEB_SEARCH_USD_PER_SEARCH = 0.01  # $10 pro 1000 Suchen

ELEVENLABS_USD_PER_1K_CHARS = 0.08


def model_by_key(key: str) -> VideoModel:
    for m in VIDEO_MODELS:
        if m.key == key:
            return m
    raise KeyError(key)


def claude_cost(input_tokens: int, output_tokens: int, web_searches: int = 0,
                model: str = DEFAULT_CLAUDE_MODEL) -> float:
    """Kosten einer Claude-Anfrage aus den Verbrauchsangaben (usage) der API."""
    _, price_in, price_out = CLAUDE_MODELS.get(model, CLAUDE_MODELS[DEFAULT_CLAUDE_MODEL])
    return (input_tokens * price_in + output_tokens * price_out) / 1e6 + web_searches * WEB_SEARCH_USD_PER_SEARCH


def estimate_script_cost(fact_check: bool = True, model: str = DEFAULT_CLAUDE_MODEL) -> tuple[float, float]:
    """Grobe Spanne (min, max) für Recherche + Skript mit Claude (Schätzung, nicht gemessen)."""
    research = (claude_cost(15_000, 1_500, 3, model), claude_cost(45_000, 5_000, 4, model))
    script = (claude_cost(4_000, 2_000, 0, model), claude_cost(8_000, 6_000, 0, model))
    if not fact_check:
        return script
    return research[0] + script[0], research[1] + script[1]


def estimate_ai_video_cost(model_key: str, ai_moments: int,
                           seconds_each: float = SECONDS_PER_AI_MOMENT) -> tuple[float, float]:
    """Kosten für die KI-Clips im Hybrid-Modus (min = alles klappt, max = mit 20 % Reserve)."""
    m = model_by_key(model_key)
    base = ai_moments * m.clip_cost(seconds_each)
    return base, base * (1 + RETRY_RESERVE)


def estimate(seconds: int, model_key: str = "stock", ai_moments: int = 3, fact_check: bool = True,
             has_claude: bool = True, premium_voice: bool = False,
             claude_model: str = DEFAULT_CLAUDE_MODEL) -> dict:
    """Komplette Schätzung für ein Video – wird vor jedem Start in der App angezeigt."""
    items = []
    if has_claude:
        lo, hi = estimate_script_cost(fact_check, claude_model)
        short = CLAUDE_MODELS.get(claude_model, CLAUDE_MODELS[DEFAULT_CLAUDE_MODEL])[0].split(" –")[0]
        items.append({"label": (f"Recherche, Faktencheck & Skript ({short})" if fact_check
                                else f"Skript ({short})"), "min": lo, "max": hi})
    else:
        items.append({"label": "Skript: Demo-Skript (kein Claude-Schlüssel)", "min": 0.0, "max": 0.0})

    if premium_voice:
        cost = seconds * 15 / 1000 * ELEVENLABS_USD_PER_1K_CHARS
        items.append({"label": "KI-Stimme (ElevenLabs)", "min": cost, "max": cost * 1.1})
    else:
        items.append({"label": "KI-Stimme (Microsoft Edge)", "min": 0.0, "max": 0.0})

    m = model_by_key(model_key)
    if m.usd_per_second > 0:
        lo, hi = estimate_ai_video_cost(model_key, ai_moments)
        billed = m.billed_seconds(SECONDS_PER_AI_MOMENT)
        items.append({"label": f"{ai_moments} KI-Szenen à {billed} s: {m.name}", "min": lo, "max": hi})
        items.append({"label": "Restliche Szenen: Stockvideos (Pexels)", "min": 0.0, "max": 0.0})
    else:
        items.append({"label": "Videoszenen: Stockvideos (Pexels)", "min": 0.0, "max": 0.0})
    items.append({"label": "Schnitt, Untertitel, Musik, Soundeffekte (lokal)", "min": 0.0, "max": 0.0})

    total_lo = sum(i["min"] for i in items)
    total_hi = sum(i["max"] for i in items)
    return {"items": items, "total_min": round(total_lo, 2), "total_max": round(total_hi, 2),
            "currency": "USD", "paid": total_hi > 0, "prices_as_of": PRICES_AS_OF}


def catalog(seconds: int = 45, ai_moments: int = 3, claude_model: str = DEFAULT_CLAUDE_MODEL) -> list[dict]:
    """Alle Modelle mit Kosten für ein fertiges Video (inkl. Claude) im Hybrid-Modus."""
    script_lo, script_hi = estimate_script_cost(True, claude_model)
    rows = []
    for m in VIDEO_MODELS:
        v_lo, v_hi = estimate_ai_video_cost(m.key, ai_moments) if m.usd_per_second else (0.0, 0.0)
        rows.append({**asdict(m),
                     "billed_seconds": m.billed_seconds(SECONDS_PER_AI_MOMENT) if m.usd_per_second else 0,
                     "video_min": round(v_lo, 2), "video_max": round(v_hi, 2),
                     "total_min": round(v_lo + script_lo, 2), "total_max": round(v_hi + script_hi, 2)})
    return rows
