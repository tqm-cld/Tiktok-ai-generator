# Projektstand (11. November 2026)

## Was fertig ist

- **6 Formate:** Finde den Imposter, Mysteriöse Überwachungskamera, Du entscheidest, Unmöglicher Kriminalfall,
  Das unendliche Level, Fakten-Doku – je mit eigener Dramaturgie, Kulisse, Grafik, Musik, Sprechweise und Untertitelstil
  (`tiktok_generator/formats.py`).
- **Kostenloser Skript-Generator** für alle Rätsel-Formate, logisch geprüft, mit Serien-Unterstützung (`offline.py`).
  Mit Claude-Schlüssel: frei geschriebene Skripte zur eigenen Idee inkl. Seriengedächtnis (`story.py`).
- **Serien:** Figuren, Regeln, Cliffhanger, Vorschau, keine Wiederholungen (`series.py`, Daten in `data/series/`).
- **Render-Pipeline:** 1080 × 1920, gezeichnete Kulissen (`scenes.py`), Grafiken in sicheren Zonen (`overlays.py`),
  4 Untertitelstile (`subtitles.py`), Kamerafahrten/Farblooks (`video.py`).
- **Audio:** 10 Stimmen + Sprechweisen + Figurenstimmen, 6 selbst komponierte Musikstile, Soundeffekte, Ducking,
  Normalisierung, Limiter (`audio.py`, `sfx.py`, `voice.py`).
- **Qualitätskontrolle** vor und nach dem Export mit Auto-Korrektur (`qc.py`).
- **Web-App** (`app.py`, `templates/index.html`): Formatkarten, Probehören, Serienmodus, Szenenvorschau, Kosten,
  Fortschritt, QC-Bericht, nächste Folge; iPhone-tauglich, Zugangscode im WLAN.
- **Kostenschutz:** Zustimmung vor jedem kostenpflichtigen Schritt (auch beim Planen), Monatsbudget, Ausgabenbuch.
- Hybrid-Modus vorbereitet, **kein** kostenpflichtiges KI-Videomodell eingebaut.

Details und ehrlicher Funktionsstatus: `docs/FORMATE.md`.

## Offene Aufgaben

1. **Auf Windows testen** (siehe unten): ein Video pro Format erstellen, Stimme hören, Download prüfen.
2. **Stimmen und Pexels** unter echten Bedingungen prüfen (in der Entwicklungsumgebung gesperrt).
3. ⚠️ *kostenpflichtig, nur mit Zustimmung:* Claude-Schlüssel eintragen und die neuen Formate mit eigener Idee testen
   (ca. 0,01–0,15 $ pro Skript; Fakten-Doku 0,18–0,47 $).
4. ⚠️ *kostenpflichtig, nur mit Zustimmung:* echtes KI-Videomodell (z. B. Seedance) einbauen.
5. Optional: mehr Grundfälle für den kostenlosen Kriminalfall-Generator (derzeit 6).

## Auf Windows starten

1. Python 3.10+ (Häkchen „Add python.exe to PATH“) und Git installieren.
2. Bestehender Ordner aktualisieren – im Projektordner (z. B. `C:\tiktok_app`) in PowerShell:
   ```
   git pull origin claude/tiktok-ai-video-generator-m6ldsj
   ```
   (Falls der Ordner aus einem ZIP stammt: neu herunterladen bzw. `git clone …` wie unten und die Datei `.env` hinüberkopieren.)
   Neu klonen:
   ```
   git clone https://github.com/tqm-cld/Tiktok-ai-generator.git
   cd Tiktok-ai-generator
   git checkout claude/tiktok-ai-video-generator-m6ldsj
   ```
3. **Doppelklick auf `start.bat`** → Browser öffnet <http://127.0.0.1:8765>. Keine neuen Pakete nötig.
4. Mit Claude Code weiterarbeiten: im Projektordner `claude` starten und z. B. sagen:
   *„Lies PROJEKTSTAND.md und docs/FORMATE.md, dann testen wir die Formate auf Windows.“*

Schlüssel (Claude, Pexels) gehören in die Datei `.env` oder in ⚙️ Einstellungen – nie auf GitHub.
