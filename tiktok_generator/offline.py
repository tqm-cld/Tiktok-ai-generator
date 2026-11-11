"""Kostenlose Skript-Generatoren für alle Formate (ohne API-Schlüssel, komplett offline).

Die Generatoren setzen Folgen aus geprüften Bausteinen zusammen. Die Rätsel sind so konstruiert,
dass sie immer eindeutig lösbar sind: Genau ein Hinweis widerspricht genau einer Aussage.
Mit einem Claude-Schlüssel werden die Skripte stattdessen frei geschrieben (story.py) – vielfältiger,
aber kostenpflichtig.

Serien: Die Generatoren bekommen den bisherigen Serienverlauf und
  - behalten Schauplatz und Figuren bei,
  - lösen den letzten Cliffhanger auf,
  - vermeiden Kombinationen, die es in der Serie schon gab (signature).
"""

import random

from .story import Character, Scene, Source, Story, demo_story

WORDS_PER_SECOND = 2.55   # deutsches Sprechtempo der Edge-Stimmen (+5 %)


def _s(text, kind="narration", on_screen="", speaker="", sfx="none", emphasis="", query="", prompt="",
       change="", optional=False):
    scene = Scene(text=text, kind=kind, on_screen=on_screen, speaker=speaker, sfx=sfx, emphasis=emphasis,
                  visual_query=query, visual_prompt=prompt, change=change)
    scene._optional = optional  # nur intern: darf zum Kürzen weggelassen werden
    return scene


def _fit(scenes: list[Scene], seconds: int) -> list[Scene]:
    """Lässt optionale Shots (von hinten) weg, bis die Länge ungefähr passt."""
    budget = seconds * WORDS_PER_SECOND
    scenes = list(scenes)
    for i in range(len(scenes) - 1, -1, -1):
        if sum(len(s.text.split()) for s in scenes) <= budget:
            break
        if getattr(scenes[i], "_optional", False):
            scenes.pop(i)
    return scenes


def _used(series: dict | None) -> set[str]:
    return {e.get("signature", "") for e in (series or {}).get("episodes", [])}


def _last(series: dict | None) -> dict:
    eps = (series or {}).get("episodes", [])
    return eps[-1] if eps else {}


def _recent(series: dict | None, field_idx: int, n: int) -> set[str]:
    """Bausteine (Teil der Kennung) der letzten n Folgen – die sollen nicht sofort wiederkommen."""
    eps = (series or {}).get("episodes", [])[-n:]
    return {e.get("signature", "").split("|")[field_idx] for e in eps if e.get("signature", "").count("|") >= field_idx}


def _pick_unique(rng: random.Random, make, used: set[str], tries: int = 60):
    """Würfelt so lange, bis eine noch nie verwendete Kombination herauskommt."""
    result = None
    for _ in range(tries):
        result = make()
        if result[0] not in used:
            return result
    return result


# ====================================================================== Finde den Imposter

NAMES = [("Lena", "Technikerin"), ("Jonas", "Pilot"), ("Mira", "Ärztin"), ("Tarek", "Koch"),
         ("Sophie", "Forscherin"), ("Ben", "Sicherheitschef"), ("Nora", "Funkerin"), ("Emil", "Mechaniker"),
         ("Aylin", "Biologin"), ("Paul", "Ingenieur"), ("Greta", "Navigatorin"), ("Yusuf", "Elektriker")]

IMPOSTER_SETTINGS = [
    {"name": "Raumstation Aurora", "art": "der", "query": "space station interior", "rooms": [
        ("das Labor", "im Labor"), ("die Kommandobrücke", "auf der Kommandobrücke"), ("der Lagerraum", "im Lagerraum"),
        ("der Fitnessraum", "im Fitnessraum"), ("die Bordküche", "in der Bordküche"), ("der Funkraum", "im Funkraum")]},
    {"name": "Forschungsstation Polaris", "art": "der", "query": "antarctic research station", "rooms": [
        ("das Labor", "im Labor"), ("der Generatorraum", "im Generatorraum"), ("der Funkraum", "im Funkraum"),
        ("die Kantine", "in der Kantine"), ("das Lager", "im Lager"), ("die Bibliothek", "in der Bibliothek")]},
    {"name": "Nachtzug Orion", "art": "dem", "query": "night train interior", "rooms": [
        ("der Speisewagen", "im Speisewagen"), ("der Gepäckwagen", "im Gepäckwagen"), ("das Abteil 7", "im Abteil 7"),
        ("der Barwagen", "im Barwagen"), ("der Schlafwagen", "im Schlafwagen"), ("der Postwagen", "im Postwagen")]},
    {"name": "Kreuzfahrtschiff Meridian", "art": "dem", "query": "cruise ship corridor night", "rooms": [
        ("der Maschinenraum", "im Maschinenraum"), ("die Bordbibliothek", "in der Bordbibliothek"),
        ("die Brücke", "auf der Brücke"), ("das Pooldeck", "auf dem Pooldeck"),
        ("die Bordküche", "in der Bordküche"), ("der Funkraum", "im Funkraum")]},
]
# (Akkusativ für „Jemand hat …“, Bildschirmtext, Nominativ für „… wird …“)
INCIDENTS = [("den Hauptgenerator sabotiert", "SABOTAGE AM GENERATOR", "der Hauptgenerator sabotiert"),
             ("den Tresorschlüssel gestohlen", "SCHLÜSSEL GESTOHLEN", "der Tresorschlüssel gestohlen"),
             ("die Funkanlage zerstört", "FUNK ZERSTÖRT", "die Funkanlage zerstört"),
             ("das Logbuch gelöscht", "LOGBUCH GELÖSCHT", "das Logbuch gelöscht"),
             ("die Alarmanlage abgeschaltet", "ALARM ABGESCHALTET", "die Alarmanlage abgeschaltet"),
             ("die Notfallkarte gestohlen", "KARTE GESTOHLEN", "die Notfallkarte gestohlen")]
TIMES = ["21:50", "22:10", "23:40", "00:25", "01:15", "02:30"]
ACTIVITIES = ["habe Messwerte geprüft", "habe Kaffee gekocht", "habe Vorräte gezählt", "habe Funksprüche abgehört",
              "habe eine Pause gemacht", "habe Kabel repariert", "habe Berichte geschrieben"]
IMPOSTER_HOOKS = ["Einer von ihnen lügt. Findest du den Imposter?", "Vier Alibis. Eins ist gelogen. Siehst du es?",
                  "Nur ein Detail verrät den Imposter. Pass genau auf.", "Ein Satz ist eine Lüge. Welcher?"]


def _imposter(rng, seconds, idea, episode, series, choice):
    used = _used(series)
    state = (series or {}).get("state", {})
    setting = IMPOSTER_SETTINGS[state.get("setting_idx", rng.randrange(len(IMPOSTER_SETTINGS)))]
    crew = [tuple(c) for c in state.get("crew", [])] or rng.sample(NAMES, 4)
    last = _last(series)
    if last.get("culprit"):                      # Serie: der letzte Imposter ist weg, jemand Neues kommt
        crew = [c for c in crew if c[0] != last["culprit"]]
        newcomers = [n for n in NAMES if n[0] not in {c[0] for c in crew} and n[0] != last["culprit"]]
        crew.append(rng.choice(newcomers))
    crew = crew[:4]

    recent_inc = _recent(series, 2, 4)

    announced = next((i for i in INCIDENTS if i[1] == state.get("next_incident")), None) if last else None

    def make():
        imp = rng.randrange(len(crew))
        # die in der letzten Folge angekündigte Tat wird auch umgesetzt (keine Widersprüche)
        incident = announced or rng.choice([i for i in INCIDENTS if i[1] not in recent_inc] or INCIDENTS)
        clue_type = rng.choice(["locked", "dark", "camera", "screens"])
        time = rng.choice(TIMES)
        rooms = rng.sample(setting["rooms"], len(crew) + 1)   # letzter Raum = Tatort
        sig = f"imp|{crew[imp][0]}|{incident[1]}|{clue_type}|{rooms[imp][0]}"
        return sig, imp, incident, clue_type, time, rooms

    sig, imp, incident, clue_type, time, rooms = _pick_unique(rng, make, used)
    crime_room = rooms[-1]
    acts = rng.sample(ACTIVITIES, len(crew))
    hour = int(time[:2])
    statements, clue, clue_screen, reason, logic = [], "", "", "", []
    witness = (imp + 1) % len(crew)

    for i, (name, role) in enumerate(crew):
        room_nom, room_in = rooms[i]
        text = f"Ich war um {time} {room_in} und {acts[i]}."
        if i == imp:
            if clue_type == "dark":
                text = f"Ich war um {time} {room_in} und habe in Ruhe ein Buch gelesen."
            elif clue_type == "camera":
                text = f"Ich war um {time} mit {crew[witness][0]} {rooms[witness][1]}."
            elif clue_type == "screens":
                text = f"Ich war {room_in} und habe um {time} die Nachrichten auf dem Bildschirm gesehen."
        elif i == witness and clue_type == "camera":
            text = f"Ich war um {time} allein {room_in} und {acts[i]}."
        statements.append(_s(text, "statement", on_screen=text, speaker=name,
                             sfx="whoosh" if i else "none", emphasis=name, query=setting["query"]))

    imp_name = crew[imp][0]
    room_nom, room_in = rooms[imp]
    if clue_type == "locked":
        clue = f"Hinweis: {room_nom[0].upper() + room_nom[1:]} war die ganze Nacht abgeschlossen. Niemand kam hinein."
        clue_screen = f"{room_nom.upper()} WAR ABGESCHLOSSEN"
        reason = f"{imp_name} behauptet, {room_in} gewesen zu sein – aber der Raum war die ganze Nacht abgeschlossen."
        logic = [f"{room_nom} war abgeschlossen", f"{imp_name} sagt, {room_in} gewesen zu sein", f"also lügt {imp_name}"]
    elif clue_type == "dark":
        clue = f"Hinweis: Um {time} fiel {room_in} der Strom aus. Dort war es stockdunkel."
        clue_screen = f"{time}: STROMAUSFALL {room_in.upper()}"
        reason = f"{imp_name} will {room_in} gelesen haben – aber dort war um {time} wegen des Stromausfalls alles dunkel."
        logic = [f"Stromausfall {room_in} um {time}", f"{imp_name} will dort gelesen haben", "im Dunkeln liest niemand"]
    elif clue_type == "camera":
        clue = f"Hinweis: Die Kamera {rooms[witness][1]} zeigt um {time} nur eine Person: {crew[witness][0]}."
        clue_screen = f"KAMERA: NUR {crew[witness][0].upper()}"
        reason = f"{imp_name} sagt, mit {crew[witness][0]} zusammen gewesen zu sein – die Kamera zeigt {crew[witness][0]} aber allein."
        logic = [f"Kamera zeigt nur {crew[witness][0]}", f"{crew[witness][0]} sagt: allein", f"{imp_name} behauptet das Gegenteil"]
    else:
        clue = f"Hinweis: Zwischen {hour:02d}:00 und {(hour + 1) % 24:02d}:00 Uhr waren alle Bildschirme wegen eines Updates aus."
        clue_screen = "ALLE BILDSCHIRME WAREN AUS"
        reason = f"{imp_name} will um {time} Nachrichten auf dem Bildschirm gesehen haben – da waren alle Bildschirme aus."
        logic = ["alle Bildschirme waren aus", f"{imp_name} will um {time} Nachrichten gesehen haben", f"also lügt {imp_name}"]

    intro = []
    if last.get("culprit"):
        intro.append(_s(f"Nach dem Verrat von {last['culprit']} ist neu an Bord: {crew[-1][0]}, {crew[-1][1]}.",
                        "narration", on_screen=f"NEU AN BORD: {crew[-1][0].upper()}", query=setting["query"],
                        optional=True))
    hook = rng.choice(IMPOSTER_HOOKS)
    scenes = [
        _s(hook, "hook", on_screen="FINDE DEN IMPOSTER", sfx="boom", emphasis="Imposter", query=setting["query"]),
        *intro,
        _s(f"{setting['name']}, {time} Uhr. Jemand hat {incident[0]}.", "narration",
           on_screen=f"{time} · {incident[1]}", sfx="impact", emphasis=incident[0].split()[-1], query=setting["query"]),
        *statements,
        _s(clue, "clue", on_screen=clue_screen, sfx="clue", emphasis="Hinweis", query=setting["query"]),
        _s("Wer ist der Imposter? Du hast drei Sekunden.", "countdown", on_screen="3", sfx="countdown",
           emphasis="Imposter"),
        _s(f"Es war {imp_name}! {reason}", "reveal", on_screen=f"IMPOSTER: {imp_name.upper()}", speaker="",
           sfx="reveal", emphasis=imp_name),
    ]
    nxt_inc = rng.choice([i for i in INCIDENTS if i != incident])
    nxt = nxt_inc[2]
    teaser = f"Folge {episode + 1}: Auf {setting['art']} {setting['name']} wird {nxt}. Wer lügt diesmal?"
    if episode:
        scenes.append(_s(teaser, "teaser", on_screen=f"NÄCHSTE FOLGE: {episode + 1}", sfx="whoosh", optional=True))
    if len(crew) > 3:  # die 4. Aussage darf beim Kürzen wegfallen, wenn sie für das Rätsel nicht nötig ist
        statements[-1]._optional = imp != len(crew) - 1 and witness != len(crew) - 1

    story = Story(
        title=f"Finde den Imposter: {incident[1].title()}", hook_title="FINDE DEN IMPOSTER",
        scenes=_fit(scenes, seconds), hashtags=["imposter", "rätsel", "findedenimposter", "logikrätsel"],
        format="imposter", setting=setting["name"],
        characters=[Character(name=n, role=r) for n, r in crew],
        culprit=imp_name, solution=reason, logic=logic,
        summary=f"{setting['name']}, {time}: {incident[2]}. Imposter war {imp_name}.",
        next_teaser=teaser if episode else "", signature=sig,
    )
    # Figuren, die durch das Kürzen nicht mehr vorkommen, aus der Besetzung nehmen
    spoken = {s.speaker for s in story.scenes if s.speaker}
    story.characters = [c for c in story.characters if c.name in spoken or c.name == imp_name]
    story._state = {"setting_idx": IMPOSTER_SETTINGS.index(setting), "crew": [list(c) for c in crew],
                    "next_incident": nxt_inc[1]}
    return story


# ====================================================================== Überwachungskamera

CCTV_LOCATIONS = [
    {"name": "Hotelflur, 3. Stock", "cam": "CAM 03", "query": "empty hotel hallway night"},
    {"name": "Tiefgarage, Ebene minus zwei", "cam": "CAM 07", "query": "empty parking garage night"},
    {"name": "Museum, Saal B", "cam": "CAM 12", "query": "museum hall night"},
    {"name": "Lagerhalle Nord", "cam": "CAM 02", "query": "warehouse night"},
    {"name": "Schulflur im Altbau", "cam": "CAM 05", "query": "school corridor night"},
    {"name": "Bürogebäude, Treppenhaus", "cam": "CAM 09", "query": "office stairwell night"},
]
CCTV_CHANGES = {
    "door": ("Achte auf die Tür ganz hinten.", "Die Tür am Ende war zu. Jetzt steht sie einen Spalt offen – niemand ist durchgegangen."),
    "chair": ("Achte auf den Stuhl an der Wand.", "Der Stuhl stand an der Wand. Jetzt steht er mitten im Raum – ohne dass ihn jemand berührt hat."),
    "shadow": ("Achte auf die Wand rechts.", "An der Wand rechts ist ein zweiter Schatten. Aber im Bild ist niemand."),
    "light": ("Achte auf die Lampe hinten.", "Die Lampe hinten ist plötzlich aus. Niemand war am Schalter."),
    "clock": ("Achte auf die Uhr an der Wand.", "Die Uhr an der Wand ist um genau dreizehn Minuten zurückgesprungen."),
}
CCTV_REVEAL_SCREEN = {"door": "DIE TÜR STEHT OFFEN", "chair": "DER STUHL HAT SICH BEWEGT",
                      "shadow": "EIN ZWEITER SCHATTEN", "light": "DIE LAMPE IST AUS", "clock": "DIE UHR SPRANG ZURÜCK"}
CCTV_HOOKS = ["Diese Aufnahme wurde nie erklärt. Schau genau hin.", "Eine Sache verändert sich in diesem Video. Findest du sie?",
              "Der Wachmann hat es übersehen. Du auch?"]


def _cctv(rng, seconds, idea, episode, series, choice):
    used = _used(series)
    last = _last(series)
    state = (series or {}).get("state", {})
    loc_idx = state.get("loc_idx", rng.randrange(len(CCTV_LOCATIONS)))
    loc = CCTV_LOCATIONS[loc_idx]

    recent_ch = _recent(series, 2, 2)

    def make():
        change = rng.choice([c for c in CCTV_CHANGES if c not in recent_ch] or list(CCTV_CHANGES))
        hour = rng.choice([1, 2, 3, 4])
        minute = rng.randrange(0, 40)
        return f"cctv|{loc_idx}|{change}|{hour}", change, hour, minute

    sig, change, hour, minute = _pick_unique(rng, make, used)
    t = [f"{hour:02d}:{minute + d:02d}" for d in (0, 3, 7, 12)]
    hint, reveal = CCTV_CHANGES[change]
    cam = loc["cam"]
    scenes = [_s(rng.choice(CCTV_HOOKS), "hook", on_screen="NICHT ERKLÄRBAR", sfx="boom", emphasis="nie")]
    if last.get("open_threads"):
        scenes.append(_s(f"Nach dem Ausfall um {last.get('end_time', '03:00')} lief die Kamera wieder. Aber etwas war anders.",
                         "cctv", on_screen=f"{cam} · WIEDER ONLINE", sfx="glitch", optional=True))
    scenes += [
        _s(f"{cam}, {t[0]} Uhr. {loc['name']}. Alles ist ruhig.", "cctv", on_screen=f"{cam} · {t[0]}",
           emphasis="ruhig", query=loc["query"]),
        _s(f"{t[1]} Uhr. Das Licht flackert kurz. Sonst passiert nichts.", "cctv", on_screen=f"{cam} · {t[1]}",
           sfx="glitch", emphasis="flackert", query=loc["query"], optional=True),
        _s(hint, "clue", on_screen=hint.rstrip(".").upper(), sfx="clue",
           emphasis=hint.split()[-1].rstrip("."), query=loc["query"]),
        _s(f"{t[2]} Uhr. Und jetzt sieh noch einmal hin.", "cctv", on_screen=f"{cam} · {t[2]}", emphasis="jetzt",
           change=change, query=loc["query"]),
        _s("Hast du es bemerkt? Drei, zwei, eins.", "countdown", on_screen="3", sfx="countdown", change=change,
           emphasis="bemerkt"),
        _s(reveal, "reveal", on_screen=CCTV_REVEAL_SCREEN[change], sfx="reveal", change=change, emphasis=reveal.split()[1]),
        _s(f"Um {t[3]} fiel die Kamera aus. Was danach passierte, siehst du in Teil {episode + 1 if episode else 2}.",
           "cliffhanger", on_screen="SIGNAL VERLOREN", sfx="glitch", change=change, emphasis="Kamera"),
    ]
    story = Story(
        title=f"Überwachungskamera: {loc['name']}", hook_title="SCHAU GENAU HIN",
        scenes=_fit(scenes, seconds), hashtags=["überwachungskamera", "mystery", "fiktion", "hastdusgesehen"],
        format="cctv", setting=loc["name"], solution=reveal, logic=[hint, reveal],
        summary=f"{cam} im {loc['name']}: {reveal}", open_threads=[f"Was geschah nach {t[3]} Uhr?"],
        resolved_threads=list(last.get("open_threads", []))[:1],
        next_teaser=f"Teil {episode + 1 if episode else 2}: Was die Kamera nach {t[3]} Uhr zeigte.", signature=sig,
    )
    story._state = {"loc_idx": loc_idx}
    story._extra = {"end_time": t[3]}
    return story


# ====================================================================== Du entscheidest

SURVIVAL = [
    {"key": "wueste", "name": "Wüste", "query": "desert dunes heat", "hook": "Kein Wasser, kein Netz, kein Weg. Was tust du?",
     "stages": [
         {"text": ["Dein Jeep bleibt mitten in der Wüste stehen.", "Es ist Mittag, über vierzig Grad.",
                   "Du hast nur noch einen Liter Wasser.", "Dein Handy zeigt: kein Netz.",
                   "Am Horizont flimmern Lichter. Oder ist das nur die Hitze?"],
          "choices": ["A: Im Schatten des Jeeps auf Hilfe warten", "B: Nachts zu den Lichtern am Horizont laufen",
                      "C: Mit dem Rückspiegel Lichtsignale geben"],
          "outcomes": {"A": "Du bleibst im Schatten. Kluge Wahl: Ein Fahrzeug sieht man aus der Luft viel leichter als einen Menschen.",
                       "B": "Du läufst nachts los. Doch die Lichter sind viel weiter weg, als sie aussahen.",
                       "C": "Du blinkst mit dem Spiegel. Ein Flugzeug wackelt mit den Flügeln – hat es dich gesehen?"}},
         {"text": ["Am Abend zieht ein Sandsturm auf.", "Der Wind wird so laut, dass du dein eigenes Rufen nicht hörst.",
                   "Die Sicht sinkt auf wenige Meter.", "Dein Wasser reicht noch für einen halben Tag."],
          "choices": ["A: Im Auto Schutz suchen", "B: Eine Mulde graben und Gesicht bedecken", "C: Weitergehen, bevor er da ist"],
          "outcomes": {"A": "Im Auto bist du geschützt. Am Morgen hörst du ein Motorengeräusch.",
                       "B": "Du überstehst den Sturm, aber deine Spuren sind verschwunden.",
                       "C": "Der Sturm holt dich ein. Du verlierst die Orientierung."}}]},
    {"key": "schnee", "name": "Schneesturm", "query": "snow storm mountains", "hook": "Minus zwanzig Grad. Und es wird dunkel.",
     "stages": [
         {"text": ["Beim Wandern in den Bergen zieht ein Schneesturm auf.", "Der Weg ist verschwunden.",
                   "Deine Finger werden taub, das Handy ist bei drei Prozent.",
                   "In einer Stunde ist es dunkel.", "Unten im Tal siehst du ein schwaches Licht."],
          "choices": ["A: Eine Schneehöhle graben", "B: Den eigenen Spuren zurück folgen", "C: Zur Hütte im Tal absteigen"],
          "outcomes": {"A": "Du gräbst eine Höhle. Darin ist es deutlich wärmer als draußen im Wind.",
                       "B": "Deine Spuren sind schon halb zugeweht. Du findest nur die Hälfte.",
                       "C": "Du steigst ab. Doch das Licht, das du für die Hütte hieltst, bewegt sich."}},
         {"text": ["Mitten in der Nacht hörst du draußen Schritte im Schnee.", "Sie kommen näher.",
                   "Dann ist es still.", "Deine Lampe hat noch für zehn Minuten Strom."],
          "choices": ["A: Rufen", "B: Leise bleiben und warten", "C: Mit der Lampe nachsehen"],
          "outcomes": {"A": "Jemand ruft zurück. Ein Suchtrupp!", "B": "Die Schritte entfernen sich wieder.",
                       "C": "Im Lampenlicht siehst du Spuren. Sie führen direkt zu deiner Höhle."}}]},
    {"key": "insel", "name": "Schiffbruch", "query": "deserted island beach", "hook": "Du wachst an einem fremden Strand auf.",
     "stages": [
         {"text": ["Nach einem Sturm wachst du an einem einsamen Strand auf.", "Vom Boot ist nur ein Seil übrig.",
                   "Die Sonne brennt, und du hast seit Stunden nichts getrunken.",
                   "Hinter dir beginnt dichter Wald.", "Über dir kreisen Möwen. Irgendwo muss Land sein."],
          "choices": ["A: Zuerst Süßwasser suchen", "B: Ein großes SOS in den Sand legen", "C: Auf den Hügel klettern"],
          "outcomes": {"A": "Du findest einen Bach im Wald. Wasser zuerst – das ist richtig so.",
                       "B": "Dein SOS ist riesig. Aber über dir fliegt heute niemand.",
                       "C": "Vom Hügel aus siehst du Rauch auf der anderen Seite der Insel."}},
         {"text": ["In der Nacht hörst du Stimmen am Strand.", "Sie sprechen eine Sprache, die du nicht kennst.",
                   "Ein Boot liegt im seichten Wasser.", "Sie haben dich noch nicht gesehen."],
          "choices": ["A: Zu ihnen gehen", "B: Verstecken und beobachten", "C: Ein Feuer anzünden"],
          "outcomes": {"A": "Es sind Fischer. Sie sind überrascht, dich zu sehen.",
                       "B": "Sie laden Kisten ab und verschwinden wieder.",
                       "C": "Das Feuer sieht man weit. Die Stimmen kommen näher."}}]},
]


def _entscheidung(rng, seconds, idea, episode, series, choice):
    state = (series or {}).get("state", {})
    sc = SURVIVAL[state.get("scenario_idx", rng.randrange(len(SURVIVAL)))]
    stage_idx = state.get("stage", 0)
    last = _last(series)
    choice = (choice or "A").strip().upper()[:1]
    scenes = [_s(sc["hook"], "hook", on_screen="DU ENTSCHEIDEST", sfx="boom", emphasis="du", query=sc["query"])]
    resolved = []
    if last and stage_idx > 0:
        prev = sc["stages"][min(stage_idx - 1, len(sc["stages"]) - 1)]
        outcome = prev["outcomes"].get(choice, prev["outcomes"]["A"])
        chosen = next((c for c in prev["choices"] if c.startswith(choice)), prev["choices"][0])
        scenes.append(_s(f"Ihr habt entschieden: {chosen[3:]}.", "narration", on_screen=f"EURE WAHL: {choice}",
                         sfx="choice", emphasis=choice, query=sc["query"]))
        scenes.append(_s(outcome, "narration", on_screen="", emphasis=outcome.split()[1], query=sc["query"]))
        resolved = [f"Entscheidung {choice}"]
    if stage_idx < len(sc["stages"]):
        stage = sc["stages"][stage_idx]
    else:  # nach den vorbereiteten Etappen: allgemeine Fortsetzung
        stage = {"text": ["Ein neuer Tag beginnt.", "Doch etwas hat sich verändert: Deine Vorräte reichen nur noch bis heute Abend."],
                 "choices": ["A: Vorräte einteilen und warten", "B: Neue Vorräte suchen", "C: Ein Signal setzen"],
                 "outcomes": {}}
    for i, line in enumerate(stage["text"]):
        scenes.append(_s(line, "narration", sfx="whoosh" if i else "impact", emphasis=line.split()[-1].rstrip(".?"),
                         query=sc["query"], optional=(i in (1, 3))))
    choices = stage["choices"]
    scenes.append(_s("Was machst du? " + " ".join(f"{c[:1]}: {c[3:]}." for c in choices), "choice",
                     on_screen=" | ".join(choices), sfx="choice", emphasis="du", query=sc["query"]))
    scenes.append(_s("Schreib A, B oder C in die Kommentare. Die meisten Stimmen entscheiden, wie es weitergeht.",
                     "cliffhanger", on_screen="A, B ODER C?", sfx="riser", emphasis="Kommentare"))
    sig = f"choice|{sc['key']}|{stage_idx}|{choice}"
    story = Story(
        title=f"Du entscheidest: {sc['name']} – Teil {stage_idx + 1}", hook_title="DU ENTSCHEIDEST",
        scenes=_fit(scenes, seconds), hashtags=["duentscheidest", "survival", "interaktiv", sc["key"]],
        format="entscheidung", setting=sc["name"], choices=choices,
        summary=" ".join(stage["text"]), open_threads=[f"Wahl zwischen {', '.join(c[:1] for c in choices)}"],
        resolved_threads=resolved, next_teaser="Die Kommentare entscheiden, wie es weitergeht.", signature=sig,
    )
    story._state = {"scenario_idx": SURVIVAL.index(sc), "stage": stage_idx + 1}
    return story


# ====================================================================== Kriminalfall

CASES = [
    {"title": "Der Diamant im verschlossenen Saal", "query": "museum hall night",
     "incident": "In der Nacht verschwand der Blaue Diamant aus einem Saal, der von innen verriegelt war.",
     "suspects": [("Wachmann", "Ich habe den Saal um Mitternacht verriegelt und bin die ganze Zeit am Eingang geblieben."),
                  ("Restauratorin", "Ich war die ganze Nacht unten in meiner Werkstatt im Keller."),
                  ("Direktor", "Ich war zu Hause und habe geschlafen.")],
     "evidence": ["BEWEIS A: Nasse Fußspuren führen vom Lüftungsgitter quer durch den Saal.",
                  "BEWEIS B: Der Lüftungsschacht im Saal führt direkt in den Keller.",
                  "BEWEIS C: Das Gitter ist voller Gips – derselbe Gips liegt in der Werkstatt."],
     "culprit": 1, "solution": "Die Restauratorin kam durch den Lüftungsschacht aus ihrer Werkstatt – das beweisen Gips und Spuren."},
    {"title": "Das vertauschte Testament", "query": "old office desk typewriter",
     "incident": "Das Testament des Millionärs wurde über Nacht durch eine Fälschung ersetzt.",
     "suspects": [("Neffe", "Ich war im Ausland. Mein Flug ist erst heute Morgen gelandet."),
                  ("Haushälterin", "Ich habe nur Staub gewischt. Ich kann nicht einmal Schreibmaschine schreiben."),
                  ("Anwalt", "Ich habe das Original nie angefasst. Es lag im Safe.")],
     "evidence": ["BEWEIS A: Die Fälschung wurde auf einer Schreibmaschine getippt.",
                  "BEWEIS B: In der Küche liegen Einkaufslisten – alle mit Schreibmaschine getippt, in der Handschrift der Haushälterin unterschrieben."],
     "culprit": 1, "solution": "Die Haushälterin lügt: Sie tippt ihre Einkaufslisten selbst auf der Schreibmaschine."},
    {"title": "Der Läufer mit dem perfekten Alibi", "query": "marathon runners city",
     "incident": "Während des Stadtmarathons verschwand der Siegerpokal aus dem Zielzelt.",
     "suspects": [("Läufer", "Ich bin die ganze Zeit gelaufen. Meine Zeitmessung beweist es."),
                  ("Fotografin", "Ich stand am Kilometer zehn und habe fotografiert."),
                  ("Sanitäter", "Ich war im Sanitätszelt, das ist neben dem Ziel.")],
     "evidence": ["BEWEIS A: Laut Zeitchip lief der Läufer fünf Kilometer in acht Minuten.",
                  "BEWEIS B: Der Weltrekord für fünf Kilometer liegt bei über zwölf Minuten."],
     "culprit": 0, "solution": "Der Läufer hat abgekürzt: Fünf Kilometer in acht Minuten sind unmöglich – er war in der Zeit am Zielzelt."},
    {"title": "Das Gemälde im Schnee", "query": "snowy cabin night",
     "incident": "Aus einer Berghütte wurde ein Gemälde gestohlen. Es schneite die ganze Nacht.",
     "suspects": [("Nachbar", "Ich bin erst heute Morgen mit dem Auto angekommen."),
                  ("Skilehrerin", "Ich war bis zehn Uhr abends auf der Piste und dann im Hotel."),
                  ("Hüttenwirt", "Ich habe die ganze Nacht hinter der Bar gestanden.")],
     "evidence": ["BEWEIS A: Es schneite von zweiundzwanzig Uhr bis sechs Uhr morgens.",
                  "BEWEIS B: Auf dem Auto des Nachbarn liegen zwanzig Zentimeter Schnee."],
     "culprit": 0, "solution": "Der Nachbar lügt: Bei so viel Schnee auf dem Auto stand es die ganze Nacht schon vor der Hütte."},
    {"title": "Die Uhr des Kapitäns", "query": "ship deck sunset",
     "incident": "Auf einem Segelschiff verschwand um zwanzig Uhr fünfzehn die goldene Taschenuhr des Kapitäns.",
     "suspects": [("Steuermann", "Ich stand am Steuer, das kann die ganze Crew bezeugen."),
                  ("Passagierin", "Ich habe um zwanzig Uhr fünfzehn den Sonnenuntergang an Deck fotografiert."),
                  ("Schiffskoch", "Ich war in der Kombüse und habe das Abendessen gekocht.")],
     "evidence": ["BEWEIS A: An diesem Tag ging die Sonne um neunzehn Uhr zwei unter.",
                  "BEWEIS B: Die Kajüte des Kapitäns liegt direkt neben der Kabine der Passagierin."],
     "culprit": 1, "solution": "Die Passagierin lügt: Um zwanzig Uhr fünfzehn war die Sonne längst untergegangen."},
    {"title": "Das Rezept aus dem Tresor", "query": "restaurant kitchen night",
     "incident": "Das geheime Rezept eines Sternerestaurants wurde aus dem Tresor kopiert – ohne Spuren.",
     "suspects": [("Souschef", "Ich kenne den Tresorcode nicht. Den kennt nur die Chefin."),
                  ("Kellnerin", "Ich habe nach Feierabend nur die Tische gedeckt."),
                  ("Lieferant", "Ich war nur kurz da und habe Gemüse gebracht.")],
     "evidence": ["BEWEIS A: Der Tresorcode ist das Geburtsdatum der Chefin.",
                  "BEWEIS B: Im Spind des Souschefs hängt eine Geburtstagskarte für die Chefin – mit Datum."],
     "culprit": 0, "solution": "Der Souschef kannte das Geburtsdatum der Chefin – und damit den Tresorcode."},
]
SURNAMES = ["Weber", "Krause", "Brandt", "Hoffmann", "Vogel", "Keller", "Lorenz", "Sommer", "Winter", "Albrecht", "Berger", "Fuchs"]


def _krimi(rng, seconds, idea, episode, series, choice):
    used = _used(series)

    recent_cases = _recent(series, 1, 4)

    def make():
        idx = rng.choice([i for i in range(len(CASES)) if str(i) not in recent_cases] or list(range(len(CASES))))
        names = rng.sample(SURNAMES, 3)
        return f"krimi|{idx}|{names[CASES[idx]['culprit']]}", idx, names

    sig, idx, names = _pick_unique(rng, make, used)
    case = CASES[idx]
    people = [(f"{role} {names[i]}", role) for i, (role, _) in enumerate(case["suspects"])]
    culprit = people[case["culprit"]][0]
    scenes = [
        _s("Ein Verbrechen, das unmöglich scheint. Kannst du es lösen?", "hook", on_screen="UNMÖGLICHER FALL",
           sfx="boom", emphasis="unmöglich", query=case["query"]),
        _s(case["incident"], "narration", on_screen=case["title"].upper(), sfx="impact", query=case["query"]),
    ]
    for i, (role, statement) in enumerate(case["suspects"]):
        scenes.append(_s(statement, "suspect", on_screen=statement.rstrip("."), speaker=people[i][0],
                         sfx="whoosh", emphasis=names[i], query=case["query"]))
    for i, ev in enumerate(case["evidence"]):
        scenes.append(_s(ev.split(": ", 1)[1], "evidence", on_screen=ev, sfx="clue", query=case["query"],
                         emphasis=ev.split(": ", 1)[1].split()[1]))
    scenes += [
        _s("Wer war es? Denk nach. Drei, zwei, eins.", "countdown", on_screen="3", sfx="countdown", emphasis="Wer"),
        _s(f"Es war {culprit}! {case['solution'].replace(case['suspects'][case['culprit']][0], culprit, 1)}",
           "reveal", on_screen=f"TÄTER: {culprit.upper()}", sfx="reveal", emphasis=names[case["culprit"]]),
    ]
    return Story(
        title=f"Kriminalfall: {case['title']}", hook_title="LÖST DU DEN FALL?",
        scenes=_fit(scenes, seconds), hashtags=["krimi", "detektiv", "rätsel", "kriminalfall"],
        format="krimi", setting=case["title"],
        characters=[Character(name=n, role=r) for n, r in people],
        culprit=culprit, solution=case["solution"], logic=[e for e in case["evidence"]],
        summary=f"{case['title']}: Täter war {culprit}.", signature=sig,
    )


# ====================================================================== Das unendliche Level

LEVEL_ROOMS = [
    ("Das Kaufhaus", "in einem Kaufhaus, in dem alle Rolltreppen nach unten führen", "empty mall escalators night"),
    ("Der Hotelflur", "in einem Hotelflur, dessen Zimmernummern nie enden", "empty hotel hallway"),
    ("Das Schwimmbad", "in einem leeren Schwimmbad mit warmem, summendem Licht", "empty indoor pool"),
    ("Die Schule", "in einer Schule, in der alle Uhren drei Uhr dreiunddreißig zeigen", "empty school hallway"),
    ("Das Parkhaus", "in einem Parkhaus ohne Ausgang", "empty parking garage"),
    ("Das Büro", "in einem Großraumbüro, in dem alle Telefone gleichzeitig klingeln", "empty office night"),
    ("Die Bibliothek", "in einer Bibliothek, in der jedes Buch deinen Namen trägt", "empty library"),
    ("Der Bahnhof", "an einem Bahnhof, an dem nur Züge ohne Fahrer halten", "empty train station night"),
]
LEVEL_RULES = [
    "Schau nie in einen Spiegel, der dich zuerst ansieht.", "Wenn das Licht gelb wird, bleib stehen und zähle bis zehn.",
    "Antworte nie, wenn jemand deinen Namen von hinten ruft.", "Folge den grünen Notausgängen – außer sie blinken.",
    "Iss nichts, das schon auf einem Tisch steht.", "Hörst du Musik, geh in die andere Richtung.",
    "Zähle die Türen. Ist es plötzlich eine mehr, dreh um.", "Öffne keine Tür, hinter der jemand klopft.",
    "Bleib nie länger als eine Minute im Aufzug.", "Wenn alles still wird, halt die Luft an.",
]
LEVEL_EVENTS = [
    ("Dann ruft jemand deinen Namen. Von hinten.", "Wer hat deinen Namen gerufen?"),
    ("Plötzlich zählst du eine Tür mehr als vorher.", "Woher kam die zusätzliche Tür?"),
    ("Das Licht wird gelb. Und am Ende des Gangs bewegt sich etwas.", "Was war am Ende des Gangs?"),
    ("Irgendwo klopft es. Ganz langsam. Dreimal.", "Wer hat geklopft?"),
]
LEVEL_ATMOS = ["Es ist vollkommen still. Nur das Licht summt.", "Die Luft riecht nach Staub und kaltem Metall.",
               "Irgendwo tropft Wasser. Immer im gleichen Takt.", "Deine Schritte hallen viel zu lange nach."]
LEVEL_RESOLUTIONS = ["Es war Mira – aber sie schwört, dass sie nichts gesagt hat.", "Es war nur ein Echo. Glaubst du.",
                     "Es war der Mann im gelben Regenmantel. Er ist dir gefolgt.", "Niemand. Der Gang war leer."]


def _level(rng, seconds, idea, episode, series, choice):
    used = _used(series)
    state = (series or {}).get("state", {})
    last = _last(series)
    known_rules = list((series or {}).get("facts", []))
    # Serie: genau das angekündigte nächste Level („Fortsetzung in Level n+1“)
    level_no = state["level"] + 1 if last and "level" in state else rng.randrange(1, 400)

    recent_rooms = _recent(series, 1, 3)

    def make():
        room = rng.choice([r for r in LEVEL_ROOMS if r[0] not in recent_rooms] or LEVEL_ROOMS)
        return f"level|{room[0]}|{level_no}", room

    sig, room = _pick_unique(rng, make, used)
    fresh = [r for r in LEVEL_RULES if r not in known_rules]
    new_rules = rng.sample(fresh or LEVEL_RULES, 2)
    event, thread = rng.choice(LEVEL_EVENTS)
    scenes = [_s("Wenn du hier aufwachst, gibt es nur eine Chance: die Regeln.", "hook", on_screen="DAS UNENDLICHE LEVEL",
                 sfx="boom", emphasis="Regeln", query=room[2])]
    resolved = []
    if last.get("open_threads"):
        scenes.append(_s(f"Die Frage von letztem Mal? {rng.choice(LEVEL_RESOLUTIONS)}", "narration",
                         on_screen="AUFGELÖST", sfx="reveal", query=room[2], optional=True))
        resolved = last["open_threads"][:1]
    scenes += [
        _s(f"Level {level_no}. {room[0]}.", "level", on_screen=f"LEVEL {level_no}|{room[0].upper()}", sfx="impact",
           emphasis=str(level_no), query=room[2]),
        _s(f"Du stehst {room[1]}.", "narration", emphasis=room[1].split()[-1], query=room[2]),
        _s(rng.choice(LEVEL_ATMOS), "narration", query=room[2], optional=True),
        _s("Mira ist bei dir. Sie war schon einmal hier.", "narration", on_screen="MIRA · KENNT DIE REGELN", emphasis="Mira",
           query=room[2], optional=True),
    ]
    if known_rules:
        old = rng.choice(known_rules)
        scenes.append(_s(f"Die alte Regel gilt noch: {old}", "rule", on_screen=f"ALTE REGEL: {old}", sfx="tick",
                         emphasis="alte", optional=True))
    scenes.append(_s("In deiner Tasche steckt ein Zettel. Darauf stehen die Regeln.", "narration",
                     on_screen="DIE REGELN", sfx="tick", emphasis="Regeln", optional=True))
    for i, rule in enumerate(new_rules, 1):
        scenes.append(_s(f"Regel {i}: {rule}", "rule", on_screen=f"REGEL {i}: {rule}", sfx="tick", emphasis=str(i)))
    scenes += [
        _s(event, "narration", sfx="riser", emphasis=event.split()[-1].rstrip("."), query=room[2]),
        _s(f"Mira flüstert: Das war nicht ich. Fortsetzung in Level {level_no + 1}.", "cliffhanger",
           on_screen=f"{thread} · LEVEL {level_no + 1} FOLGT", sfx="glitch", emphasis="nicht"),
    ]
    story = Story(
        title=f"Das unendliche Level {level_no}: {room[0]}", hook_title=f"LEVEL {level_no}",
        scenes=_fit(scenes, seconds), hashtags=["unendlicheslevel", "mystery", "serie", "liminalspace"],
        format="level", setting=room[0],
        characters=[Character(name="Mira", role="Begleiterin"), Character(name="Der Mann im gelben Regenmantel", role="Unbekannt")],
        facts=new_rules, open_threads=[thread], resolved_threads=resolved,
        summary=f"Level {level_no}, {room[0]}: {event}", next_teaser=f"Level {level_no + 1}: {thread}", signature=sig,
    )
    story._state = {"level": level_no}
    return story


# ====================================================================== Einstieg

GENERATORS = {"imposter": _imposter, "cctv": _cctv, "entscheidung": _entscheidung, "krimi": _krimi, "level": _level}


def generate_offline(fmt: str, seconds: int = 40, idea: str = "", episode: int = 0, series: dict | None = None,
                     seed: int | None = None, choice: str | None = None) -> Story:
    """Erzeugt ein Skript ohne KI. `episode` > 0 = Serienfolge (series enthält den bisherigen Verlauf)."""
    if fmt not in GENERATORS:
        story = demo_story(seconds)
        story.format = "fakten"
        return story
    rng = random.Random(seed if seed is not None else random.randrange(1 << 30))
    story = GENERATORS[fmt](rng, seconds, idea, episode, series, choice)
    story.episode = episode
    if series:
        story.series_id, story.series_name = series.get("id", ""), series.get("name", "")
    return story
