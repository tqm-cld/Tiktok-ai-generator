"""Qualitätskontrolle vor und nach dem Export – mit automatischer Korrektur, wo möglich.

Ergebnis ist eine Liste von Prüfpunkten mit Status:
  ok      – in Ordnung
  fixed   – Problem gefunden und automatisch behoben
  warn    – Hinweis, Video wird trotzdem erstellt
  fail    – ernstes Problem (Skript wird neu erzeugt bzw. Video neu gerendert)
"""

import re
import subprocess
from dataclasses import asdict, dataclass

import imageio_ffmpeg

HOOK_MAX_WORDS = 12


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""

    def dict(self):
        return asdict(self)


def _norm(t: str) -> str:
    return re.sub(r"[^a-zäöüß0-9 ]", "", t.lower()).strip()


# ------------------------------------------------------------------ Skript (vor dem Rendern)

def check_script(story, spec, series=None) -> list[Check]:
    from .series import check_consistency

    out: list[Check] = []
    # 1) Alle Szenen vorhanden?
    before = len(story.scenes)
    story.scenes = [s for s in story.scenes if s.text.strip()]
    if not story.scenes:
        return [Check("Szenen vorhanden", "fail", "Das Skript enthält keine Szenen.")]
    out.append(Check("Szenen vorhanden", "fixed" if len(story.scenes) < before else "ok",
                     f"{len(story.scenes)} Szenen" + (f", {before - len(story.scenes)} leere entfernt" if len(story.scenes) < before else "")))

    # 2) Wiederholungen
    seen, removed = set(), 0
    unique = []
    for s in story.scenes:
        key = _norm(s.text)
        if key in seen and s.kind not in ("countdown",):
            removed += 1
            continue
        seen.add(key)
        unique.append(s)
    story.scenes = unique
    starts = [(_norm(s.text).split() or [""])[0] for s in story.scenes]
    common = max((starts.count(w) for w in set(starts) if w not in ("ich", "du", "es", "die", "der", "das")), default=0)
    if removed:
        out.append(Check("Keine Wiederholungen", "fixed", f"{removed} doppelte Sätze entfernt"))
    elif common >= 4:
        out.append(Check("Keine Wiederholungen", "warn", f"{common} Sätze beginnen gleich"))
    else:
        out.append(Check("Keine Wiederholungen", "ok"))

    # 3) Einstieg
    first = story.scenes[0]
    fixed = []
    if first.kind != "hook":
        first.kind = "hook"
        fixed.append("erster Shot als Hook markiert")
    if not story.hook_title:
        story.hook_title = spec.name.upper()[:28]
        fixed.append("Hook-Titel ergänzt")
    if first.sfx == "none":
        first.sfx = "boom"
        fixed.append("Akzent-Sound am Anfang")
    n = len(first.text.split())
    hooky = "?" in first.text or any(ch.isdigit() for ch in first.text) or n <= 9
    status = "fixed" if fixed else ("ok" if n <= HOOK_MAX_WORDS and hooky else "warn")
    out.append(Check("Starker Einstieg", status,
                     f"Hook mit {n} Wörtern" + (f" ({', '.join(fixed)})" if fixed else "") +
                     ("" if n <= HOOK_MAX_WORDS else " – länger als empfohlen")))

    # 4) Rätsel-Logik je Format
    out.append(_check_logic(story, spec))

    # 5) Bild passt zum Text
    if spec.look == "stock" or spec.use_stock:
        missing = [s for s in story.scenes if not s.visual_query]
        for s in missing:
            s.visual_query = story.setting or story.title
        out.append(Check("Bild passt zum Text", "fixed" if missing else "warn" if spec.look == "stock" else "ok",
                         (f"{len(missing)} Suchbegriffe ergänzt. " if missing else "") +
                         ("Stockvideos werden per Suchbegriff gewählt – Passung ohne Bild-KI nur grob prüfbar."
                          if spec.look == "stock" else "Kulissen werden passend zum Format gezeichnet.")))
    else:
        out.append(Check("Bild passt zum Text", "ok", "Kulisse und Grafiken werden aus Szenentyp und Schauplatz erzeugt."))

    # 6) Länge
    words = sum(len(s.text.split()) for s in story.scenes)
    est = words / 2.55
    out.append(Check("Länge", "ok" if 28 <= est <= 62 else "warn", f"ca. {est:.0f} s ({words} Wörter)"))

    # 7) Serie
    if series:
        problems = check_consistency(series, story)
        out.append(Check("Serie ohne Widersprüche", "warn" if problems else "ok", "; ".join(problems)))
    return out


def _check_logic(story, spec) -> Check:
    fmt = story.format
    kinds = [s.kind for s in story.scenes]
    if fmt in ("imposter", "krimi"):
        names = [c.name for c in story.characters]
        speak_kind = "statement" if fmt == "imposter" else "suspect"
        speakers = [s.speaker for s in story.scenes if s.kind == speak_kind]
        clue_idx = [i for i, k in enumerate(kinds) if k in ("clue", "evidence")]
        reveal_idx = [i for i, k in enumerate(kinds) if k == "reveal"]
        problems, fixes = [], []
        if not story.culprit or story.culprit not in names:
            problems.append("Täter ist keine der Figuren")
        if story.culprit and story.culprit not in speakers:
            problems.append("Täter kommt nicht zu Wort")
        if not clue_idx:
            problems.append("kein Hinweis/Beweis")
        if not reveal_idx:
            problems.append("keine Auflösung")
        elif clue_idx and max(clue_idx) > reveal_idx[0]:
            problems.append("Hinweis kommt erst nach der Auflösung")
        if "countdown" not in kinds and reveal_idx:
            from .story import Scene
            story.scenes.insert(reveal_idx[0], Scene(text="Wer war es? Drei, zwei, eins.", kind="countdown",
                                                     on_screen="3", sfx="countdown", emphasis="Wer"))
            fixes.append("Countdown ergänzt")
        if reveal_idx and story.culprit:
            rv = story.scenes[[i for i, s in enumerate(story.scenes) if s.kind == "reveal"][0]]
            if story.culprit not in rv.text:
                rv.text = f"Es war {story.culprit}! {rv.text}"
                fixes.append("Täter in der Auflösung genannt")
        if problems:
            return Check("Rätsel logisch lösbar", "fail", "; ".join(problems))
        return Check("Rätsel logisch lösbar", "fixed" if fixes else "ok",
                     (", ".join(fixes) + ". " if fixes else "") +
                     f"Genau ein Täter ({story.culprit}), Hinweis vor der Auflösung, {len(story.logic)} Logikschritte.")
    if fmt == "cctv":
        first_change = next((i for i, s in enumerate(story.scenes) if s.change), None)
        if first_change is None:
            return Check("Rätsel logisch lösbar", "warn", "Keine sichtbare Veränderung festgelegt.")
        for s in story.scenes[first_change:]:          # Veränderung bleibt sichtbar
            s.change = s.change or story.scenes[first_change].change
        has_reveal = "reveal" in kinds[first_change:]
        return Check("Rätsel logisch lösbar", "ok" if has_reveal else "warn",
                     "Veränderung wird gezeigt und danach aufgelöst." if has_reveal else "Auflösung fehlt.")
    if fmt == "entscheidung":
        if not (2 <= len(story.choices) <= 3):
            return Check("Rätsel logisch lösbar", "fail", "Es braucht 2–3 Optionen.")
        if "choice" not in kinds:
            from .story import Scene
            story.scenes.append(Scene(text="Was machst du? " + " ".join(story.choices), kind="choice",
                                      on_screen=" | ".join(story.choices), sfx="choice"))
            return Check("Entscheidung vorhanden", "fixed", "Auswahl-Szene ergänzt")
        return Check("Entscheidung vorhanden", "ok", f"{len(story.choices)} Optionen")
    if fmt == "level":
        rules = kinds.count("rule")
        ok = "level" in kinds and rules >= 2
        return Check("Level & Regeln", "ok" if ok else "warn", f"{rules} Regeln, Level-Titel {'ja' if 'level' in kinds else 'nein'}")
    return Check("Inhalt", "ok", "Faktenvideo – Quellen werden angezeigt." if story.sources else "Faktenvideo")


# ------------------------------------------------------------------ Ton & Synchronität (nach dem Mischen)

def check_render(info, voices) -> list[Check]:
    out = []
    words = info.words
    order_ok = all(b.start >= a.start - 1e-3 for a, b in zip(words, words[1:]))
    inside = True
    for (s0, s1), v in zip(info.scene_spans, voices):
        if v.words and v.words[-1].end > (s1 - s0) + 0.25:
            inside = False
    silent = any(v.silent for v in voices)
    out.append(Check("Stimme & Untertitel synchron", "ok" if order_ok and inside else "warn",
                     ("Wortgenaue Zeitstempel der Stimme. " if not silent else
                      "Stimme offline stumm – Untertitel nach geschätztem Sprechtempo. ") +
                     ("" if order_ok and inside else "Einzelne Wörter liegen außerhalb ihrer Szene.")))
    rep = info.mix
    if rep is not None:
        if rep.voice_db > -90:
            st = "ok" if rep.music_gap_db >= 12 else "warn"
            detail = f"Musik {rep.music_gap_db:.0f} dB leiser als die Stimme (Ducking aktiv)"
        else:
            st, detail = "warn", "Stimme stumm (Offline-Test) – Musik auf Normalpegel"
        out.append(Check("Musik nicht zu laut", st, detail))
        out.append(Check("Lautstärke normalisiert", "ok" if rep.peak_db <= -0.5 else "warn",
                         f"Spitze {rep.peak_db:.1f} dBFS, Limiter aktiv" +
                         (f", {rep.clipped_before_limiter} Spitzen abgefangen" if rep.clipped_before_limiter else "")))
    return out


# ------------------------------------------------------------------ MP4-Datei (nach dem Export)

def check_mp4(path, expected: float, size=(1080, 1920)) -> list[Check]:
    """Liest die ganze Datei einmal komplett (Dekodiertest) und sucht schwarze Bilder."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        proc = subprocess.run([ffmpeg, "-hide_banner", "-v", "info", "-i", str(path), "-vf",
                               "blackdetect=d=0.4:pix_th=0.06", "-f", "null", "-"],
                              capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [Check("MP4 vollständig", "fail", f"Prüfung nicht möglich: {e}")]
    err = proc.stderr
    out = []
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    seconds = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0
    res = re.search(r"Video: h264.*?(\d{3,4})x(\d{3,4})", err)
    has_audio = "Audio: aac" in err
    decode_errors = [l for l in err.splitlines() if "error" in l.lower() and "blackdetect" not in l]
    ok = proc.returncode == 0 and seconds > 0 and abs(seconds - expected) < 1.5 and has_audio and not decode_errors
    out.append(Check("MP4 vollständig", "ok" if ok else "fail",
                     f"{seconds:.1f} s, H.264 + AAC, komplett dekodierbar" if ok else
                     f"Dauer {seconds:.1f}/{expected:.1f} s, Ton {'ja' if has_audio else 'nein'}, Fehler: {decode_errors[:2]}"))
    if res:
        w, h = int(res.group(1)), int(res.group(2))
        out.append(Check("Format 9:16", "ok" if (w, h) == tuple(size) else "fail", f"{w} × {h}"))
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
    out.append(Check("Keine schwarzen Bilder", "ok" if not blacks else "warn",
                     "" if not blacks else f"Schwarz bei {', '.join(f'{float(a):.1f}s' for a, _ in blacks[:3])}"))
    return out


def summarize(checks: list[Check]) -> str:
    bad = [c for c in checks if c.status == "fail"]
    warn = [c for c in checks if c.status == "warn"]
    fixed = [c for c in checks if c.status == "fixed"]
    if bad:
        return f"{len(bad)} Problem(e)"
    return "Alles in Ordnung" + (f" ({len(fixed)} automatisch korrigiert" if fixed else "") + \
        (f", {len(warn)} Hinweis(e)" if warn else "") + (")" if fixed else "")
