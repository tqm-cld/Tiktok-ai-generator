# 🎬 TikTok-KI-Generator

Erstellt automatisch TikTok-Kurzvideos (9:16, 30–60 Sekunden) aus:

| Baustein | Werkzeug | Kosten |
|---|---|---|
| ✍️ Geschichte | Claude (Anthropic API) | ein paar Cent pro Video |
| 🖼️ Bilder / Videoclips | Pexels API | kostenlos |
| 🗣️ KI-Stimme | Microsoft Edge TTS (`edge-tts`) | kostenlos |
| 🎵 Hintergrundmusik | deine eigenen MP3s | kostenlos (lizenzfreie Musik) |
| 💬 Animierte Untertitel | Pillow + MoviePy | kostenlos |

```
Thema ──► ① Geschichte (Claude) ──► ② Stimme + Wortzeiten (edge-tts)
                                        │
          ③ Bilder/Videos (Pexels) ◄────┘
                    │
                    ▼
   ④ Untertitel + ⑤ Musik + ⑥ Zusammenschnitt (MoviePy) ──► output/video.mp4
```

---

## 🗺️ Der Schritt-für-Schritt-Plan

Wir bauen das Programm in kleinen Etappen. Jede Etappe ist für sich testbar.

### Etappe 0 – Werkzeuge installieren (einmalig)

1. **Python 3.10 oder neuer** installieren: <https://www.python.org/downloads/>
   (Windows: beim Installieren das Häkchen **„Add Python to PATH“** setzen.)
2. **FFmpeg** installieren (für Video/Audio):
   - Windows: `winget install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
3. **Git** installieren (optional, zum Herunterladen des Projekts): <https://git-scm.com>
4. Einen Code-Editor, z. B. **VS Code**: <https://code.visualstudio.com>

Test im Terminal: `python --version` und `ffmpeg -version` sollten eine Versionsnummer zeigen.

### Etappe 1 – Projekt einrichten

```bash
git clone <URL-dieses-Repos>
cd Tiktok-ai-generator

# Eine "virtuelle Umgebung" hält die Pakete dieses Projekts getrennt vom Rest des PCs
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Etappe 2 – Erster Test im Demo-Modus (ohne Schlüssel)

```bash
python main.py --demo
```

Das erzeugt ein Video mit einer fest eingebauten Beispielgeschichte, echter KI-Stimme
und Farbverläufen als Hintergrund. Ergebnis: `output/…mp4`.
👉 Wenn das klappt, funktioniert die ganze Technik schon!

### Etappe 3 – API-Schlüssel eintragen

1. Datei `.env.example` kopieren und in `.env` umbenennen.
2. **Claude-Schlüssel**: Konto auf <https://console.anthropic.com> anlegen → „API Keys“ → Schlüssel erstellen → bei `ANTHROPIC_API_KEY=` eintragen. (Ein paar Euro Guthaben aufladen.)
3. **Pexels-Schlüssel** (kostenlos): <https://www.pexels.com/api/> → bei `PEXELS_API_KEY=` eintragen.

> ⚠️ Die Datei `.env` niemals hochladen oder teilen – sie ist schon in `.gitignore` eingetragen.

### Etappe 4 – Musik hinzufügen

Lege 2–5 lizenzfreie MP3s in `assets/music/` (z. B. von der YouTube Audio Library oder Pixabay Music).
Das Programm wählt pro Video zufällig einen Titel, macht ihn leise und blendet ihn aus.

### Etappe 5 – Echte Videos erzeugen

```bash
python main.py "Eine gruselige Geschichte über einen verlassenen Leuchtturm"
python main.py "Ein unglaublicher Fakt über das Weltall" --count 3
python main.py "Motivationsgeschichte über einen Marathonläufer" --voice de-DE-KatjaNeural
```

Pro Video entstehen im Ordner `output/`:
- `…mp4` – das fertige Video
- `…txt` – Titel + Hashtags zum Kopieren in TikTok
- `…json` – die komplette Geschichte (zum Nachlesen)

### Etappe 6 – Anpassen & verbessern (deine Spielwiese)

Alle Einstellungen stehen in `tiktok_generator/config.py`:

| Was? | Einstellung |
|---|---|
| Schriftgröße / Position der Untertitel | `font_size`, `caption_y` |
| Wörter pro Untertitel | `words_per_caption` |
| Eigene Schriftart | `.ttf`-Datei in `assets/fonts/` legen |
| Stimme / Tempo | `TTS_VOICE`, `TTS_RATE` in `.env` (alle Stimmen: `edge-tts --list-voices`) |
| Musiklautstärke | `MUSIC_VOLUME` in `.env` |
| Stil der Geschichten | `SYSTEM_PROMPT` in `tiktok_generator/story.py` |

### Etappe 7 – Ideen für später

- [ ] KI-generierte Bilder statt Stock-Fotos (z. B. über eine Bild-API)
- [ ] Übergänge zwischen den Szenen (Überblenden)
- [ ] Hook-Text groß oben in den ersten 3 Sekunden
- [ ] Liste von Themen aus einer Datei abarbeiten (Batch-Modus)
- [ ] Automatisch zeitgesteuert jeden Tag ein Video erzeugen

---

## 📁 Aufbau des Projekts

```
main.py                    ← Startpunkt: steuert die 6 Schritte
tiktok_generator/
  config.py                ← alle Einstellungen
  story.py                 ← ① Geschichte mit Claude
  voice.py                 ← ② KI-Stimme + Wortzeitstempel
  media.py                 ← ③ Pexels-Videos/-Bilder (oder Farbverlauf)
  subtitles.py             ← ④ animierte Untertitel
  music.py                 ← ⑤ Hintergrundmusik
  video.py                 ← ⑥ Zusammenschnitt
assets/music/              ← deine MP3s
assets/fonts/              ← optionale eigene Schriftarten
output/                    ← fertige Videos
```

## 🛟 Häufige Probleme

| Problem | Lösung |
|---|---|
| `ffmpeg not found` | FFmpeg installieren (Etappe 0) und Terminal neu öffnen |
| `ModuleNotFoundError` | virtuelle Umgebung aktivieren und `pip install -r requirements.txt` |
| „stummer Testmodus“ | keine Internetverbindung zu Microsoft TTS – Internet prüfen |
| Video zu kurz/lang | Thema genauer formulieren oder `TTS_RATE` ändern |
| Nur Farbverläufe | `PEXELS_API_KEY` fehlt oder ist falsch |

## ⚖️ Hinweise

- Nutze nur Musik und Material, für das du die Rechte hast. Pexels-Inhalte sind frei nutzbar.
- TikTok verlangt, dass KI-generierte Inhalte als solche gekennzeichnet werden
  (beim Hochladen „KI-generierter Inhalt“ aktivieren).
