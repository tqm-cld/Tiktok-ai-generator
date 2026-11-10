"""Schritt 1: Ein spannendes, faktengeprüftes Skript für ein KI-Faktenvideo.

Ablauf mit Claude (zwei Anfragen):
  1. Recherche: Claude sucht im Web nach den Fakten zur Frage und notiert geprüfte
     Kernaussagen mit Zahlen – inklusive Unsicherheiten und verbreiteter Irrtümer.
  2. Skript: Aus diesen Notizen entsteht das Skript mit starkem Hook, kurzen Shots,
     Bildbeschreibungen für die Videoszenen und passenden Soundeffekten.

Die Quellen-Links stammen direkt aus der Websuche (nicht von Claude ausgedacht).
"""

from typing import Literal

from pydantic import BaseModel, Field

from .config import Config

SfxName = Literal["none", "whoosh", "impact", "riser", "tick", "boom"]


class StoryError(RuntimeError):
    """Verständliche Fehlermeldung, wenn das Skript nicht erstellt werden konnte."""


class Scene(BaseModel):
    text: str = Field(description="Gesprochener Text dieses Shots: 1 kurzer Satz, max. ca. 14 Wörter")
    visual_query: str = Field(description="2-4 englische Stichwörter für die Stock-Video-Suche, z.B. 'earth from space'")
    visual_prompt: str = Field(
        description="Englischer, filmischer Prompt für ein KI-Video dieses Shots: Motiv, Bewegung, Kamera, Licht. "
                    "Ohne Text/Schrift im Bild. z.B. 'slow aerial push-in over a stormy ocean, dramatic lighting'"
    )
    sfx: SfxName = Field(description="Soundeffekt zu Beginn des Shots: impact/boom für Schock-Momente, "
                                     "riser vor einer Enthüllung, tick für Zahlen/Zeit, whoosh für schnelle Wechsel, sonst none")
    emphasis: str = Field(description="Das wichtigste Wort dieses Satzes (genau so geschrieben wie im Text), "
                                      "wird im Untertitel farbig hervorgehoben. Leer lassen, wenn keins.")


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
- visual_prompt: filmisch, viel Bewegung, realistisch, auf Englisch, ohne Text im Bild."""


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


def research_facts(topic: str, cfg: Config, client) -> tuple[str, list[Source]]:
    """Schritt 1a: Faktenrecherche mit der Websuche von Claude."""
    messages = [{"role": "user", "content": f"Frage für das Video: {topic}"}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
    response = None
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
        if response.stop_reason != "pause_turn":
            break
        messages = [messages[0], {"role": "assistant", "content": response.content}]

    if response.stop_reason == "refusal":
        raise StoryError("❌ Zu dieser Frage konnte keine Recherche durchgeführt werden. Probiere eine andere Frage.")
    notes = "\n".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
    if not notes:
        raise StoryError("❌ Die Recherche hat keine Ergebnisse geliefert. Bitte erneut versuchen.")
    return notes, _collect_sources(response.content)


def generate_story(topic: str, cfg: Config, seconds: int | None = None, fact_check: bool = True) -> Story:
    """Erzeugt ein faktengeprüftes Skript. Ohne API-Schlüssel gibt es ein Demo-Skript."""
    if not cfg.anthropic_api_key:
        print("  ⚠ Kein ANTHROPIC_API_KEY gefunden → Demo-Skript wird verwendet.")
        return demo_story(seconds)

    import anthropic

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    min_words, max_words, shots = _length_targets(seconds, cfg)

    try:
        notes, sources = research_facts(topic, cfg, client) if fact_check else ("", [])
        prompt = (
            f"Thema/Frage: {topic}\n"
            f"Sprache: {cfg.language}\n"
            f"Länge: insgesamt {min_words} bis {max_words} gesprochene Wörter in {shots} Shots "
            f"(Video ca. {seconds or 45} Sekunden).\n"
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

    draft = response.parsed_output
    if response.stop_reason == "refusal" or draft is None:
        raise StoryError("❌ Claude hat zu diesem Thema kein Skript geschrieben. Probiere ein anderes Thema.")
    return Story(**draft.model_dump(), sources=sources, fact_notes=notes)


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


def _s(text, query, prompt, sfx="none", emphasis=""):
    return Scene(text=text, visual_query=query, visual_prompt=prompt, sfx=sfx, emphasis=emphasis)


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
               "earth from space", "slow cinematic push-in on planet earth rotating in space, sun flare", "boom", "fünf"),
            _s("Am Äquator rast du gerade mit rund 1670 Kilometern pro Stunde durchs All.",
               "city aerial timelapse", "fast aerial flyover of a city at the equator, motion blur, golden hour", "whoosh", "1670"),
            _s("Du spürst es nur nicht, weil sich alles um dich herum mitbewegt.",
               "people walking street", "people walking calmly on a sunny street, handheld camera", "none", "mitbewegt"),
            _s("Doch wenn der Boden plötzlich stoppt, bewegt sich alles andere weiter.",
               "train braking", "high speed train braking hard, sparks flying, dramatic low angle", "impact", "weiter"),
            _s("Menschen, Autos – alles, was nicht fest verankert ist, würde nach Osten geschleudert.",
               "storm debris wind", "debris and cars blown sideways by extreme wind, slow motion", "boom", "geschleudert"),
            _s("Die Luft rast weiter – Winde viel stärker als der schlimmste Tornado.",
               "tornado", "massive tornado tearing across plains, dark storm clouds, epic scale", "whoosh", "Tornado"),
            _s("Selbst die stärksten Tornados erreichen nur gut 320 Kilometer pro Stunde.",
               "storm clouds timelapse", "timelapse of violent storm clouds rotating, lightning", "tick", "320"),
            _s("Und die Ozeane? Sie würden als riesige Flutwellen über die Küsten schwappen.",
               "huge ocean waves", "gigantic ocean wave crashing over a coastline, aerial, dramatic", "impact", "Flutwellen"),
            _s("Aber hier kommt die Wendung: An den Polen würdest du kaum etwas merken.",
               "arctic ice", "slow drone shot over calm arctic ice field, soft light", "riser", "Polen"),
            _s("Denn dort drehst du dich fast auf der Stelle.",
               "north pole snow", "person standing alone on snowy polar landscape, camera orbiting", "none", "Stelle"),
            _s("Zum Glück ist das reine Theorie: Es gibt nichts, was die Erde so abrupt stoppen könnte.",
               "galaxy stars", "camera pulling back from earth into a starfield, epic, cinematic", "boom", "Theorie"),
        ],
    )
