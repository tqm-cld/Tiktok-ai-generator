"""Schritt 1: Ein spannendes, faktengeprüftes Skript für ein KI-Faktenvideo.

Ablauf mit Claude (zwei Anfragen):
  1. Recherche: Claude sucht im Web nach den Fakten zur Frage und notiert geprüfte
     Kernaussagen mit Zahlen – inklusive Unsicherheiten und verbreiteter Irrtümer.
  2. Skript: Aus diesen Notizen entsteht das Skript mit starkem Hook, kurzen Shots,
     Bildbeschreibungen für die Videoszenen und passenden Soundeffekten.

Die Quellen-Links stammen direkt aus der Websuche (nicht von Claude ausgedacht).
"""

from typing import Literal

from pydantic import BaseModel, Field, PrivateAttr

from .config import Config
from .costs import CLAUDE_MODELS, DEFAULT_CLAUDE_MODEL, claude_cost

SfxName = Literal["none", "whoosh", "impact", "riser", "tick", "boom", "clue", "countdown", "choice", "reveal", "glitch"]

# Szenentypen: bestimmen, welche Grafik über dem Bild liegt (siehe overlays.py)
SceneKind = Literal["hook", "narration", "statement", "clue", "countdown", "choice", "reveal",
                    "level", "rule", "cctv", "evidence", "suspect", "cliffhanger", "teaser"]


class StoryError(RuntimeError):
    """Verständliche Fehlermeldung, wenn das Skript nicht erstellt werden konnte."""


class Scene(BaseModel):
    text: str = Field(description="Gesprochener Text dieses Shots: 1 kurzer Satz, max. ca. 14 Wörter")
    visual_query: str = Field(default="", description="2-4 englische Stichwörter für die Stock-Video-Suche, z.B. 'earth from space'")
    visual_prompt: str = Field(
        default="", description="Englischer, filmischer Prompt für ein KI-Video dieses Shots: Motiv, Bewegung, Kamera, Licht. "
                    "Ohne Text/Schrift im Bild. z.B. 'slow aerial push-in over a stormy ocean, dramatic lighting'"
    )
    sfx: SfxName = Field(default="none", description="Soundeffekt zu Beginn des Shots: impact/boom für Schock-Momente, "
                                     "riser vor einer Enthüllung, tick für Zahlen/Zeit, whoosh für schnelle Wechsel, "
                                     "clue bei Hinweisen, countdown beim Countdown, choice bei Entscheidungen, "
                                     "reveal bei der Auflösung, glitch bei Kamera-Störungen, sonst none")
    emphasis: str = Field(default="", description="Das wichtigste Wort dieses Satzes (genau so geschrieben wie im Text), "
                                      "wird im Untertitel farbig hervorgehoben. Leer lassen, wenn keins.")
    ai_moment: bool = Field(default=False, description="true nur für die wichtigsten Momente (Hook, Schock/Höhepunkt, "
                                                       "Wendung) – nur diese bekommen eine KI-generierte Videoszene")
    kind: SceneKind = Field(default="narration", description="Art des Shots – bestimmt die Grafik im Bild")
    speaker: str = Field(default="", description="Name der Figur, die spricht (leer = Erzähler)")
    on_screen: str = Field(default="", description="Kurzer Text für die Grafik im Bild (max. ca. 12 Wörter): "
                                                   "Aussage, Hinweis, Regel, Countdown-Zahl, Uhrzeit …")
    change: str = Field(default="", description="Nur Überwachungskamera: Objekt, das sich ab diesem Shot verändert hat "
                                                "(door, chair, shadow, light, clock), sonst leer")
    _optional: bool = PrivateAttr(default=False)


class Character(BaseModel):
    name: str
    role: str = Field(default="", description="Rolle/Beruf, z. B. 'Ärztin'")
    look: str = Field(default="", description="Kurze englische Beschreibung des Aussehens")
    voice: str = Field(default="", description="Stimme (wird automatisch vergeben)")


class Source(BaseModel):
    title: str
    url: str


class Story(BaseModel):
    title: str
    hook_title: str = ""
    scenes: list[Scene]
    hashtags: list[str]
    sources: list[Source] = []
    fact_notes: str = ""
    script_cost_usd: float = 0.0          # tatsächliche Claude-Kosten (aus den Verbrauchsangaben der API)

    # --- Formate & Serien ---
    format: str = "fakten"
    setting: str = ""                     # Schauplatz
    characters: list[Character] = []
    choices: list[str] = []               # "Du entscheidest": Antwortmöglichkeiten
    solution: str = ""                    # Rätsel: Lösung in einem Satz
    logic: list[str] = []                 # Rätsel: Schlussfolgerungskette (Hinweis → Schluss)
    culprit: str = ""                     # Imposter/Krimi: Name der gesuchten Person
    series_id: str = ""
    series_name: str = ""
    episode: int = 0
    summary: str = ""                     # 1-2 Sätze Zusammenfassung der Folge
    open_threads: list[str] = []          # offene Cliffhanger
    resolved_threads: list[str] = []      # in dieser Folge aufgelöste Cliffhanger
    next_teaser: str = ""                 # Vorschau auf die nächste Folge
    facts: list[str] = []                 # neue, feste Tatsachen der Serienwelt (z. B. Regeln)
    signature: str = ""                   # interne Kennung, um Wiederholungen zu vermeiden
    _state: dict = PrivateAttr(default_factory=dict)   # Serienzustand (nur Offline-Generator)
    _extra: dict = PrivateAttr(default_factory=dict)

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.scenes)


class _ScriptDraft(BaseModel):
    """Das, was Claude im zweiten Schritt ausfüllt."""
    title: str = Field(description="Kurzer Videotitel")
    hook_title: str = Field(description="Max. 6 Wörter, groß oben im Video in den ersten Sekunden, z.B. 'DIE ERDE STOPPT?'")
    scenes: list[Scene]
    hashtags: list[str] = Field(description="3-5 Hashtags ohne #")


RESEARCH_SYSTEM = """Du bist Faktenprüfer für ein Wissensvideo.
Recherchiere mit der Websuche verlässliche Quellen (Raumfahrtagenturen, Universitäten, Behörden,
Fachmedien, Lexika). Antworte auf Deutsch als knappe Faktennotiz:
- 6-12 Kernfakten mit konkreten Zahlen und Einheiten
- bei hypothetischen Fragen: was die Physik/Forschung dazu sagt und was nur Schätzung ist
- verbreitete Irrtümer, die NICHT ins Video sollen
- offene Unsicherheiten
Kein Skript, keine Einleitung."""

SCRIPT_SYSTEM = """Du schreibst Skripte für virale deutsche KI-Wissensvideos (TikTok, 9:16).
Stil: spannend wie eine Dokumentation, emotional, aber sachlich korrekt.
Regeln:
- Shot 1 ist ein extrem starker Hook (Frage, Schockzahl oder "Stell dir vor ..."), der in 2 Sekunden fesselt.
- Danach steigende Spannung, ein überraschender Wendepunkt, am Ende eine Pointe oder ein Aha-Moment.
- Jeder Shot = ein kurzer, gesprochener Satz. Keine Emojis, keine Regieanweisungen im Text.
- Zahlen ausschreiben, wie man sie spricht (z. B. "eintausendsechshundert Kilometer pro Stunde" vermeiden,
  lieber "über 1600 Kilometer pro Stunde").
- Verwende NUR Fakten aus den Recherche-Notizen. Kennzeichne Gedankenexperimente und Schätzungen als solche
  ("Forscher schätzen ...", "theoretisch ..."). Erfinde keine Zahlen.
- visual_prompt: filmisch, viel Bewegung, realistisch, auf Englisch, ohne Text im Bild.
- ai_moment: Markiere genau so viele Shots wie verlangt – immer Shot 1 (Hook), dann Schock-/Höhepunkt und Wendung.
  Nur diese Shots werden als teure KI-Videoszene erzeugt (ca. 4 Sekunden): ihr visual_prompt muss ein einziges,
  klares Motiv mit starker Bewegung beschreiben. Alle anderen Shots kommen aus Stockvideos – dort muss
  visual_query ein leicht zu findendes Alltagsmotiv sein."""


def _length_targets(seconds: int | None, cfg: Config) -> tuple[int, int, int]:
    seconds = seconds or 45
    # ca. 2,4 gesprochene Wörter pro Sekunde, kurze Shots von ca. 3-4 Sekunden
    return int(seconds * 2.1), int(seconds * 2.45), max(6, min(16, round(seconds / 3.5)))


def _collect_sources(content) -> list[Source]:
    """Sammelt die tatsächlich zitierten Quellen (Fallback: alle Suchtreffer)."""
    cited, found = {}, {}
    for block in content:
        btype = getattr(block, "type", "")
        if btype == "text":
            for c in getattr(block, "citations", None) or []:
                url = getattr(c, "url", None)
                if url:
                    cited.setdefault(url, getattr(c, "title", None) or url)
        elif btype == "web_search_tool_result":
            results = getattr(block, "content", None)
            if isinstance(results, list):
                for r in results:
                    url = getattr(r, "url", None)
                    if url:
                        found.setdefault(url, getattr(r, "title", None) or url)
    chosen = cited or found
    return [Source(title=t, url=u) for u, t in list(chosen.items())[:8]]


def usage_cost(response, requested_model: str) -> float:
    """Berechnet die tatsächlichen Kosten einer Antwort aus `response.usage`."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0.0
    tokens_in = (getattr(usage, "input_tokens", 0) or 0) + (getattr(usage, "cache_creation_input_tokens", 0) or 0) \
        + (getattr(usage, "cache_read_input_tokens", 0) or 0)
    tokens_out = getattr(usage, "output_tokens", 0) or 0
    tool_use = getattr(usage, "server_tool_use", None)
    searches = (getattr(tool_use, "web_search_requests", 0) or 0) if tool_use else 0
    model = getattr(response, "model", None) or requested_model
    if model not in CLAUDE_MODELS:  # z. B. Ersatzmodell nach einer Ablehnung → mit dem teuersten Preis rechnen
        model = DEFAULT_CLAUDE_MODEL
    return claude_cost(tokens_in, tokens_out, searches, model)


def pick_ai_moments(scenes: list[Scene], count: int) -> list[bool]:
    """Wählt genau `count` Shots für KI-Videoszenen: Hook zuerst, dann die vom Skript markierten,
    dann nach Wucht des Soundeffekts (boom > impact > riser > ...)."""
    if count <= 0 or not scenes:
        return [False] * len(scenes)
    weight = {"boom": 4, "impact": 3, "riser": 2, "whoosh": 1, "tick": 1, "none": 0}
    order = sorted(range(1, len(scenes)),
                   key=lambda i: (not scenes[i].ai_moment, -weight.get(scenes[i].sfx, 0), i))
    chosen = {0, *order[:max(0, count - 1)]}
    return [i in chosen for i in range(len(scenes))]


def research_facts(topic: str, cfg: Config, client) -> tuple[str, list[Source], float]:
    """Schritt 1a: Faktenrecherche mit der Websuche von Claude."""
    messages = [{"role": "user", "content": f"Frage für das Video: {topic}"}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 4}]
    response, cost = None, 0.0
    for _ in range(4):  # "pause_turn" = Claude ist noch nicht fertig → weitermachen lassen
        response = client.beta.messages.create(
            model=cfg.claude_model,
            max_tokens=16000,
            system=RESEARCH_SYSTEM,
            messages=messages,
            tools=tools,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        cost += usage_cost(response, cfg.claude_model)
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": response.content}]

    if response.stop_reason == "refusal":
        raise StoryError("❌ Zu dieser Frage konnte keine Recherche durchgeführt werden. Probiere eine andere Frage.")
    notes = "\n".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
    if not notes:
        raise StoryError("❌ Die Recherche hat keine Ergebnisse geliefert. Bitte erneut versuchen.")
    return notes, _collect_sources(response.content), cost


def generate_story(topic: str, cfg: Config, seconds: int | None = None, fact_check: bool = True,
                   ai_moments: int = 3) -> Story:
    """Erzeugt ein faktengeprüftes Skript. Ohne API-Schlüssel gibt es ein Demo-Skript."""
    if not cfg.anthropic_api_key:
        print("  ⚠ Kein ANTHROPIC_API_KEY gefunden → Demo-Skript wird verwendet.")
        return demo_story(seconds)

    import anthropic

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    min_words, max_words, shots = _length_targets(seconds, cfg)

    try:
        notes, sources, cost = research_facts(topic, cfg, client) if fact_check else ("", [], 0.0)
        prompt = (
            f"Thema/Frage: {topic}\n"
            f"Sprache: {cfg.language}\n"
            f"Länge: insgesamt {min_words} bis {max_words} gesprochene Wörter in {shots} Shots "
            f"(Video ca. {seconds or 45} Sekunden).\n"
            f"KI-Momente: markiere genau {max(1, ai_moments)} Shots mit ai_moment=true.\n"
        )
        if notes:
            prompt += f"\nGeprüfte Recherche-Notizen (einzige Faktenbasis):\n<notizen>\n{notes}\n</notizen>\n"
        response = client.beta.messages.parse(
            model=cfg.claude_model,
            max_tokens=16000,
            system=SCRIPT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_format=_ScriptDraft,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        raise StoryError("❌ Der Claude-API-Schlüssel ist ungültig – bitte in den Einstellungen prüfen.")
    except anthropic.RateLimitError:
        raise StoryError("❌ Zu viele Anfragen oder kein Guthaben mehr – kurz warten oder Guthaben aufladen.")
    except anthropic.APIConnectionError:
        raise StoryError("❌ Keine Verbindung zu Claude – bitte Internetverbindung prüfen.")

    cost += usage_cost(response, cfg.claude_model)
    draft = response.parsed_output
    if response.stop_reason == "refusal" or draft is None:
        raise StoryError("❌ Claude hat zu diesem Thema kein Skript geschrieben. Probiere ein anderes Thema.")
    return Story(**draft.model_dump(), sources=sources, fact_notes=notes, script_cost_usd=round(cost, 4))


# ---------------------------------------------------------------- Demo ohne API-Schlüssel

def demo_story(seconds: int | None = None) -> Story:
    """Ein festes, von Hand geprüftes Beispielskript (kostenlos, ohne API-Schlüssel).

    Ist `seconds` angegeben, werden zuerst die verzichtbarsten Shots weggelassen, damit das Video
    ungefähr so lang wird (Hook, Wendung und Schluss bleiben immer)."""
    story = _full_demo_story()
    if not seconds:
        return story
    max_words = seconds * 2.6
    drop_order = [6, 9, 2, 3, 7]  # Indizes der Shots, auf die man am ehesten verzichten kann
    keep = list(range(len(story.scenes)))
    words = lambda: sum(len(story.scenes[i].text.split()) for i in keep)
    for idx in drop_order:
        if words() <= max_words:
            break
        keep.remove(idx)
    story.scenes = [story.scenes[i] for i in keep]
    return story


def _s(text, query, prompt, sfx="none", emphasis="", ai=False):
    return Scene(text=text, visual_query=query, visual_prompt=prompt, sfx=sfx, emphasis=emphasis, ai_moment=ai)


def _full_demo_story() -> Story:
    return Story(
        title="Was, wenn die Erde 5 Sekunden stoppt?",
        hook_title="DIE ERDE STOPPT?",
        hashtags=["wissen", "physik", "erde", "gedankenexperiment", "fakten"],
        fact_notes="Demo-Skript – Zahlen von Hand geprüft (Erdrotation am Äquator ca. 1670 km/h, "
                   "stärkste Tornado-Kategorie EF5 über 320 km/h).",
        sources=[
            Source(title="NASA – Earth Fact Sheet", url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html"),
            Source(title="NOAA – Enhanced Fujita Scale", url="https://www.spc.noaa.gov/efscale/"),
        ],
        scenes=[
            _s("Was würde passieren, wenn die Erde fünf Sekunden aufhört, sich zu drehen?",
               "earth from space", "slow cinematic push-in on planet earth rotating in space, sun flare", "boom", "fünf", True),
            _s("Am Äquator rast du gerade mit rund 1670 Kilometern pro Stunde durchs All.",
               "city aerial timelapse", "fast aerial flyover of a city at the equator, motion blur, golden hour", "whoosh", "1670"),
            _s("Du spürst es nur nicht, weil sich alles um dich herum mitbewegt.",
               "people walking street", "people walking calmly on a sunny street, handheld camera", "none", "mitbewegt"),
            _s("Doch wenn der Boden plötzlich stoppt, bewegt sich alles andere weiter.",
               "train braking", "high speed train braking hard, sparks flying, dramatic low angle", "impact", "weiter"),
            _s("Menschen, Autos – alles, was nicht fest verankert ist, würde nach Osten geschleudert.",
               "storm debris wind", "debris and cars blown sideways by extreme wind, slow motion", "boom", "geschleudert", True),
            _s("Die Luft rast weiter – Winde viel stärker als der schlimmste Tornado.",
               "tornado", "massive tornado tearing across plains, dark storm clouds, epic scale", "whoosh", "Tornado"),
            _s("Selbst die stärksten Tornados erreichen nur gut 320 Kilometer pro Stunde.",
               "storm clouds timelapse", "timelapse of violent storm clouds rotating, lightning", "tick", "320"),
            _s("Und die Ozeane? Sie würden als riesige Flutwellen über die Küsten schwappen.",
               "huge ocean waves", "gigantic ocean wave crashing over a coastline, aerial, dramatic", "impact", "Flutwellen", True),
            _s("Aber hier kommt die Wendung: An den Polen würdest du kaum etwas merken.",
               "arctic ice", "slow drone shot over calm arctic ice field, soft light", "riser", "Polen", True),
            _s("Denn dort drehst du dich fast auf der Stelle.",
               "north pole snow", "person standing alone on snowy polar landscape, camera orbiting", "none", "Stelle"),
            _s("Zum Glück ist das reine Theorie: Es gibt nichts, was die Erde so abrupt stoppen könnte.",
               "galaxy stars", "camera pulling back from earth into a starfield, epic, cinematic", "boom", "Theorie"),
        ],
    )


# ---------------------------------------------------------------- Neue Formate mit Claude

class _FormatDraft(BaseModel):
    """Das füllt Claude für die Rätsel- und Mystery-Formate aus."""
    title: str = Field(description="Kurzer Videotitel")
    hook_title: str = Field(description="Max. 5 Wörter, groß oben im Video in den ersten Sekunden")
    setting: str = Field(description="Schauplatz in wenigen Wörtern")
    characters: list[Character] = Field(description="Figuren (Name, Rolle, englische Kurzbeschreibung des Aussehens)")
    scenes: list[Scene]
    choices: list[str] = Field(description="Nur 'Du entscheidest': 2-3 Optionen mit 'A: …', sonst leer")
    culprit: str = Field(description="Imposter/Krimi: genauer Name der schuldigen Figur, sonst leer")
    solution: str = Field(description="Rätsel: Lösung in einem Satz, sonst leer")
    logic: list[str] = Field(description="Rätsel: 2-4 Schritte vom Hinweis zur Lösung, sonst leer")
    summary: str = Field(description="1-2 Sätze: was in dieser Folge passiert")
    open_threads: list[str] = Field(description="Offene Fragen/Cliffhanger, die eine spätere Folge auflösen soll")
    resolved_threads: list[str] = Field(description="Offene Fragen aus früheren Folgen, die diese Folge auflöst")
    facts: list[str] = Field(description="Neue feste Tatsachen der Serienwelt (z. B. Regeln), die später gelten")
    next_teaser: str = Field(description="Ein Satz Vorschau auf die nächste Folge")
    hashtags: list[str] = Field(description="3-5 Hashtags ohne #")


FORMAT_SYSTEM = """Du schreibst Skripte für virale deutsche TikTok-Kurzvideos (9:16, 30-45 Sekunden).
Allgemeine Regeln:
- Shot 1 (kind=hook) fesselt in unter 2 Sekunden: max. 9 Wörter.
- Jeder Shot = ein kurzer gesprochener Satz (max. ca. 16 Wörter). Natürliches, gesprochenes Deutsch.
- Spannung durch Erzählung und Timing, nicht durch Übertreibung. Keine Emojis, keine Regieanweisungen im Text.
- on_screen: kurzer Text für die Grafik (Aussage, Hinweis, Regel, Uhrzeit, Countdown-Zahl).
- speaker: Name der Figur, wenn eine Figur spricht (Text dann in Ich-Form), sonst leer (Erzähler).
- sfx passend wählen (clue bei Hinweisen, countdown beim Countdown, choice bei Entscheidungen, reveal bei der Auflösung).
- emphasis: das wichtigste Wort, genau wie im Text geschrieben.
- Alles ist fiktiv: keine echten Personen, keine echten Verbrechen, keine Gewaltdetails.
- Wiederhole keine Sätze und keine Formulierungen."""


def generate_format_story(fmt_key: str, idea: str, cfg: Config, seconds: int | None = None,
                          series: dict | None = None, choice: str | None = None) -> Story:
    """Schreibt eine Folge eines der neuen Formate mit Claude (inkl. Serien-Gedächtnis)."""
    from .formats import get_format

    spec = get_format(fmt_key)
    import anthropic

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key, timeout=120, max_retries=2)
    min_words, max_words, shots = _length_targets(seconds, cfg)
    prompt = (f"{spec.rules}\n\nIdee/Thema des Nutzers: {idea or 'frei wählen, überraschend'}\n"
              f"Länge: {min_words}-{max_words} gesprochene Wörter in ca. {shots} Shots (Video ca. {seconds or 40} s).\n")
    episode = 0
    if series:
        eps = series.get("episodes", [])
        episode = len(eps) + 1
        history = "\n".join(f"- Folge {e['episode']}: {e.get('summary', '')}" for e in eps[-10:]) or "- (noch keine)"
        chars = ", ".join(f"{c.get('name')} ({c.get('role', '')})" for c in series.get("characters", [])) or "(noch keine)"
        prompt += (f"\nSERIE „{series.get('name')}“ – schreibe Folge {episode}.\n"
                   f"Feste Figuren (gleich bleibende Namen und Rollen): {chars}\n"
                   f"Feste Tatsachen der Serienwelt (niemals widersprechen): {'; '.join(series.get('facts', [])) or '(keine)'}\n"
                   f"Bisherige Folgen:\n{history}\n"
                   f"Offene Cliffhanger (mindestens einen auflösen und in resolved_threads nennen): "
                   f"{'; '.join(series.get('open_threads', [])) or '(keine)'}\n"
                   f"Bereits verwendete Täter/Lösungen nicht wiederholen: "
                   f"{', '.join(filter(None, (e.get('culprit') for e in eps))) or '(keine)'}\n")
        if choice:
            prompt += f"Die Zuschauer haben sich für Option {choice} entschieden – beginne mit den Folgen dieser Wahl.\n"
    try:
        response = client.beta.messages.parse(
            model=cfg.claude_model, max_tokens=16000, system=FORMAT_SYSTEM,
            messages=[{"role": "user", "content": prompt}], output_format=_FormatDraft,
            output_config={"effort": "medium"}, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        )
    except anthropic.AuthenticationError:
        raise StoryError("❌ Der Claude-API-Schlüssel ist ungültig – bitte in den Einstellungen prüfen.")
    except anthropic.RateLimitError:
        raise StoryError("❌ Zu viele Anfragen oder kein Guthaben mehr – kurz warten oder Guthaben aufladen.")
    except anthropic.APITimeoutError:
        raise StoryError("❌ Claude hat nicht rechtzeitig geantwortet. Bitte gleich noch einmal versuchen.")
    except anthropic.APIConnectionError:
        raise StoryError("❌ Keine Verbindung zu Claude – bitte Internetverbindung prüfen.")
    cost = usage_cost(response, cfg.claude_model)
    draft = response.parsed_output
    if response.stop_reason == "refusal" or draft is None:
        raise StoryError("❌ Claude hat zu dieser Idee kein Skript geschrieben. Probiere eine andere Idee.")
    data = draft.model_dump()
    data["hashtags"] = data.get("hashtags") or list(spec.hashtags)
    story = Story(**data, format=spec.key, episode=episode, script_cost_usd=round(cost, 4))
    if series:
        story.series_id, story.series_name = series.get("id", ""), series.get("name", "")
    return story
