"""Schritt 1: Eine kurze Geschichte mit Claude schreiben lassen.

Die Geschichte wird in "Szenen" aufgeteilt. Jede Szene hat
  - einen Text, der vorgelesen wird, und
  - einen englischen Suchbegriff, mit dem wir ein passendes Bild/Video suchen.
"""

from pydantic import BaseModel, Field

from .config import Config


class StoryError(RuntimeError):
    """Verständliche Fehlermeldung, wenn die Geschichte nicht erstellt werden konnte."""


class Scene(BaseModel):
    text: str = Field(description="Gesprochener Text dieser Szene (1-3 kurze Sätze)")
    visual_query: str = Field(
        description="2-4 englische Stichwörter für die Stock-Video-Suche, z.B. 'dark forest night'"
    )


class Story(BaseModel):
    title: str
    scenes: list[Scene]
    hashtags: list[str]

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.scenes)


SYSTEM_PROMPT = """Du schreibst Geschichten für virale TikTok-Kurzvideos.
Regeln:
- Der erste Satz ist ein starker Hook, der sofort neugierig macht.
- Kurze, gesprochene Sätze, keine Emojis, keine Regieanweisungen.
- Ein überraschendes Ende oder eine Pointe.
- visual_query ist immer auf Englisch und beschreibt ein einfaches, filmbares Motiv."""


def generate_story(topic: str, cfg: Config, seconds: int | None = None) -> Story:
    """Erzeugt eine Geschichte. Ohne API-Schlüssel gibt es eine Demo-Geschichte."""
    if not cfg.anthropic_api_key:
        print("  ⚠ Kein ANTHROPIC_API_KEY gefunden → Demo-Geschichte wird verwendet.")
        return demo_story()

    import anthropic

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    # Gewünschte Länge: entweder fest (z.B. 45 s) oder der Bereich aus der Config.
    # Faustregel: ca. 2,3 gesprochene Wörter pro Sekunde.
    if seconds:
        min_words, max_words = int(seconds * 2.1), int(seconds * 2.4)
        length_hint = f"ca. {seconds} Sekunden"
    else:
        min_words, max_words = int(cfg.min_seconds * 2.5), int(cfg.max_seconds * 2.3)
        length_hint = f"{cfg.min_seconds}-{cfg.max_seconds} Sekunden"
    scenes = max(4, min(12, round((seconds or 45) / 6)))

    prompt = (
        f"Thema: {topic}\n"
        f"Sprache: {cfg.language}\n"
        f"Länge: insgesamt {min_words} bis {max_words} Wörter "
        f"(das Video soll {length_hint} dauern), aufgeteilt in etwa {scenes} Szenen.\n"
        "Gib außerdem 3-5 passende Hashtags ohne #-Zeichen zurück."
    )

    # messages.parse prüft die Antwort automatisch gegen unser Story-Modell.
    # "fallbacks" springt auf ein anderes Modell, falls eine Anfrage abgelehnt wird.
    try:
        response = client.beta.messages.parse(
            model=cfg.claude_model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_format=Story,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        raise StoryError("❌ Der Claude-API-Schlüssel ist ungültig – bitte in den Einstellungen prüfen.")
    except anthropic.RateLimitError:
        raise StoryError("❌ Zu viele Anfragen oder kein Guthaben mehr – kurz warten oder Guthaben aufladen.")
    except anthropic.APIConnectionError:
        raise StoryError("❌ Keine Verbindung zu Claude – bitte Internetverbindung prüfen.")

    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise StoryError("❌ Claude hat zu diesem Thema keine Geschichte geschrieben. Probiere ein anderes Thema.")
    return response.parsed_output


def demo_story(seconds: int | None = None) -> Story:
    """Eine feste Beispielgeschichte zum Testen ohne API-Schlüssel.

    Ist `seconds` angegeben, werden Szenen aus der Mitte weggelassen,
    damit das Video ungefähr so lang wird (Anfang und Ende bleiben immer)."""
    story = _full_demo_story()
    if not seconds:
        return story
    max_words = seconds * 2.6
    first, last = story.scenes[0], story.scenes[-1]
    kept, words = [first], len(first.text.split()) + len(last.text.split())
    for scene in story.scenes[1:-1]:
        n = len(scene.text.split())
        if words + n > max_words:
            break
        kept.append(scene)
        words += n
    story.scenes = kept + [last]
    return story


def _full_demo_story() -> Story:
    return Story(
        title="Der Leuchtturmwärter",
        hashtags=["gruselgeschichte", "storytime", "mystery"],
        scenes=[
            Scene(text="Jede Nacht um drei Uhr ging das Licht im alten Leuchtturm aus.",
                  visual_query="lighthouse night storm"),
            Scene(text="Dabei wohnte dort seit zwanzig Jahren niemand mehr.",
                  visual_query="abandoned lighthouse"),
            Scene(text="Also beschloss ich, eine Nacht dort oben zu verbringen.",
                  visual_query="man walking stairs flashlight"),
            Scene(text="Um zwei Uhr neunundfünfzig hörte ich Schritte auf der Treppe unter mir.",
                  visual_query="dark spiral staircase"),
            Scene(text="Langsam. Schwer. Und sie kamen immer näher.",
                  visual_query="shadow footsteps dark"),
            Scene(text="Dann erschien ein alter Mann mit einer Laterne und sah mich überrascht an.",
                  visual_query="old man lantern"),
            Scene(text="Er sagte nur: Du bist also mein Nachfolger. Und dann war er verschwunden.",
                  visual_query="fog sea night"),
            Scene(text="Seitdem mache ich jede Nacht um drei das Licht aus. Und warte.",
                  visual_query="lighthouse light beam ocean"),
        ],
    )
