"""Die Videoformate der App: Dramaturgie, Musik, Sprechweise, Untertitel- und Bildstil.

Jedes Format hat
  - Regeln für Claude (wenn ein Claude-Schlüssel eingetragen ist),
  - einen kostenlosen Offline-Generator (offline.py), der ohne Schlüssel funktioniert,
  - einen Bildstil (scenes.py) und Grafiken (overlays.py).
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class FormatSpec:
    key: str
    name: str
    icon: str                 # nur für die Oberfläche
    tagline: str
    music: str                # Musikstil (siehe audio.MUSIC_STYLES)
    voice_style: str          # Sprechweise (siehe audio.VOICE_STYLES)
    subtitle_style: str       # Untertitelstil (siehe subtitles.STYLES)
    look: str                 # Bildstil (siehe scenes.py)
    use_stock: bool           # Pexels-Stockvideos verwenden, wenn ein Schlüssel da ist
    research: bool            # Faktencheck mit Websuche
    episodic: bool            # eignet sich besonders für Serien
    default_seconds: int = 40
    hashtags: tuple = ()
    rules: str = ""           # Dramaturgie-Regeln für Claude
    idea_hint: str = ""       # Platzhalter im Eingabefeld


FORMATS: dict[str, FormatSpec] = {}


def _add(spec: FormatSpec):
    FORMATS[spec.key] = spec


_add(FormatSpec(
    key="imposter", name="Finde den Imposter", icon="🕵️", tagline="Einer lügt. Findest du ihn vor dem Countdown?",
    music="spannung", voice_style="spannung", subtitle_style="tiktok", look="lineup",
    use_stock=False, research=False, episodic=True, default_seconds=40,
    hashtags=("imposter", "rätsel", "findedenimposter", "logikrätsel"),
    idea_hint="z. B. Sabotage auf einer Raumstation",
    rules="""Format „Finde den Imposter“:
- 3 bis 4 Figuren (characters) mit Namen und Rolle. Genau EINE Figur ist der Imposter (culprit).
- Ablauf: hook → narration (Vorfall mit Uhrzeit und Ort) → je ein statement pro Figur (speaker = Name,
  on_screen = Kurzfassung des Alibis) → 1-2 clue (versteckter Hinweis, der GENAU EINER Aussage widerspricht)
  → countdown (on_screen "3") → reveal (Lösung mit Begründung) → optional cliffhanger/teaser.
- Das Rätsel muss allein aus den gezeigten Aussagen und Hinweisen eindeutig lösbar sein. Keine Tricks,
  die erst in der Auflösung neu eingeführt werden. Unschuldige Aussagen dürfen dem Hinweis NICHT widersprechen.
- logic: 2-4 Schritte, die vom Hinweis zum Imposter führen. solution: ein Satz.""",
))
_add(FormatSpec(
    key="cctv", name="Mysteriöse Überwachungskamera", icon="📹", tagline="Fiktive Aufnahmen. Bemerkst du die Veränderung?",
    music="ueberwachung", voice_style="mystery", subtitle_style="mystery", look="cctv",
    use_stock=False, research=False, episodic=True, default_seconds=38,
    hashtags=("überwachungskamera", "mystery", "creepy", "fiktion"),
    idea_hint="z. B. Hotelflur um 3 Uhr nachts",
    rules="""Format „Mysteriöse Überwachungskamera“ (klar fiktiv, keine echten Personen/Orte, kein Horror-Gore):
- Ablauf: hook → 4-6 cctv-Shots mit Uhrzeit (on_screen = Kamera + Uhrzeit, z. B. "CAM 02 · 03:14")
  → clue (worauf man achten soll) → countdown oder Frage an den Zuschauer → reveal (was sich verändert hat)
  → cliffhanger (was als Nächstes passiert).
- Spannung durch ruhige Beobachtung und eine EINZIGE subtile Veränderung (Tür, Gegenstand, Schatten, Uhr),
  nicht durch Schockeffekte. visual_prompt beschreibt die Kameraperspektive auf Englisch.""",
))
_add(FormatSpec(
    key="entscheidung", name="Du entscheidest", icon="🧭", tagline="Survival-Story – die Kommentare bestimmen, wie es weitergeht.",
    music="abenteuer", voice_style="spannung", subtitle_style="tiktok", look="landscape",
    use_stock=True, research=False, episodic=True, default_seconds=40,
    hashtags=("duentscheidest", "survival", "interaktiv", "story"),
    idea_hint="z. B. Allein in der Wüste ohne Wasser",
    rules="""Format „Du entscheidest“ (interaktive Survival-Geschichte, Du-Perspektive):
- Ablauf: hook → 4-6 narration-Shots (Lage, Gefahr, Zeitdruck) → choice-Shot mit 2 oder 3 Optionen
  (choices: kurze Texte, beginnend mit "A:", "B:", "C:") → cliffhanger: "Schreib A, B oder C in die Kommentare".
- Die Optionen müssen alle plausibel sein und unterschiedliche Risiken haben. Survival-Tipps müssen sachlich
  vertretbar sein (keine gefährlichen Ratschläge als richtig darstellen).
- Bei Fortsetzungen: Folge beginnt mit dem Ergebnis der gewählten Option (resolved_threads).""",
))
_add(FormatSpec(
    key="krimi", name="Unmöglicher Kriminalfall", icon="🔍", tagline="Verdächtige, Beweise, eine logische Lösung.",
    music="detektiv", voice_style="ruhig", subtitle_style="clean", look="board",
    use_stock=False, research=False, episodic=True, default_seconds=42,
    hashtags=("krimi", "detektiv", "rätsel", "kriminalfall"),
    idea_hint="z. B. Diebstahl in einem verschlossenen Museum",
    rules="""Format „Unmöglicher Kriminalfall“ (kurzes Detektivrätsel, fiktiv):
- 3 Verdächtige (characters), genau einer ist schuldig (culprit).
- Ablauf: hook → narration (Fall, scheinbar unmöglich) → je ein suspect-Shot pro Verdächtigem
  (speaker = Name, on_screen = Aussage/Alibi) → 2-3 evidence-Shots (on_screen = "BEWEIS A: …")
  → countdown ("Wer war es?") → reveal (Täter + Begründung über die Beweise).
- Fair Play: Alle nötigen Beweise werden VOR der Auflösung gezeigt. Die Lösung folgt logisch aus Beweis +
  Aussage. logic: 2-4 Schritte. solution: ein Satz.""",
))
_add(FormatSpec(
    key="level", name="Das unendliche Level", icon="🚪", tagline="Fortlaufende Mystery-Serie mit Leveln, Regeln und Cliffhangern.",
    music="level", voice_style="mystery", subtitle_style="mystery", look="corridor",
    use_stock=False, research=False, episodic=True, default_seconds=40,
    hashtags=("unendlicheslevel", "mystery", "serie", "liminalspace"),
    idea_hint="z. B. Ein Kaufhaus, das nachts nie endet",
    rules="""Format „Das unendliche Level“ (fortlaufende Mystery-Serie, fiktiv, ohne Gore):
- Ablauf: hook → level-Shot (on_screen = "LEVEL <Zahl>" + Name) → 2-3 narration-Shots (Ort, Atmosphäre)
  → 2-3 rule-Shots (on_screen = "REGEL n: …") → ein Ereignis, das eine Regel testet → cliffhanger.
- Wiederkehrende Figuren und bereits bekannte Regeln (facts) müssen respektiert werden – nie widersprechen.
- facts: neue Regeln dieser Folge im Wortlaut. open_threads: offene Fragen. next_teaser: ein Satz.""",
))
_add(FormatSpec(
    key="fakten", name="Fakten-Doku", icon="🌍", tagline="Faktengeprüfte Wissensvideos mit Quellen.",
    music="doku", voice_style="normal", subtitle_style="tiktok", look="stock",
    use_stock=True, research=True, episodic=False, default_seconds=40,
    hashtags=("wissen", "fakten", "lernen"),
    idea_hint="z. B. Was würde passieren, wenn die Erde 5 Sekunden aufhört, sich zu drehen?",
))

ORDER = ["imposter", "cctv", "entscheidung", "krimi", "level", "fakten"]


def get_format(key: str) -> FormatSpec:
    return FORMATS.get(key) or FORMATS["fakten"]


def list_formats() -> list[dict]:
    return [{k: v for k, v in asdict(FORMATS[key]).items() if k != "rules"} for key in ORDER]
