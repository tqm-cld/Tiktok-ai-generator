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

## 🚀 So startest du das Programm (ohne Python-Befehle)

### 1. Einmalig: Python installieren

- **Windows:** <https://www.python.org/downloads/> → „Download Python“ → Installer öffnen →
  **unbedingt das Häkchen „Add python.exe to PATH“ setzen** → „Install Now“.
- **macOS:** <https://www.python.org/downloads/> → Installer herunterladen und durchklicken.
- **Linux:** meist schon vorhanden (sonst `sudo apt install python3 python3-venv`).

FFmpeg musst du **nicht** extra installieren – es wird automatisch mitgeliefert.

### 2. Einmalig: Projekt herunterladen

Auf der GitHub-Seite des Projekts: grüner Knopf **„Code“ → „Download ZIP“** → ZIP entpacken
(z. B. in „Dokumente“). Wichtig: richtigen Branch auswählen, falls er noch nicht in `main` ist.

### 3. Starten – jedes Mal

| System | Was du tust |
|---|---|
| **Windows** | Im Projektordner **Doppelklick auf `start.bat`** |
| **macOS** | **Rechtsklick auf `start.command` → „Öffnen“** (beim ersten Mal, wegen der Sicherheitsabfrage; danach reicht Doppelklick) |
| **Linux** | Doppelklick auf `start.sh` (bzw. im Terminal `./start.sh`) |

- Beim **ersten Start** werden alle Pakete automatisch installiert – das dauert 1–3 Minuten.
  Danach startet das Programm in wenigen Sekunden.
- Es öffnet sich ein schwarzes Fenster und **der Browser öffnet sich automatisch** mit
  **<http://127.0.0.1:8765>**. Falls nicht: diese Adresse selbst in den Browser eingeben.
- Das schwarze Fenster muss offen bleiben, solange du das Programm nutzt.
  **Beenden:** Fenster schließen (oder darin `Strg + C` drücken).

### 4. Video erstellen

1. **Videothema** eingeben (oder einen der Vorschläge anklicken).
2. **Länge** mit dem Schieberegler wählen (30–60 Sekunden).
3. **„✨ Video erstellen“** klicken.
4. Der Fortschrittsbalken zeigt jeden Schritt: Geschichte → Stimme → Bilder → Rendern.
   Ein Video dauert je nach Computer ca. **1–3 Minuten**.
5. Danach kannst du das Video **direkt ansehen**, mit **„⬇️ MP4 herunterladen“** speichern und
   die **Beschreibung mit Hashtags kopieren**. Unter „Meine Videos“ findest du alle bisherigen Videos.

Die Videos liegen außerdem im Ordner `output/`.

### 5. Einmalig: Schlüssel eintragen (für echte KI-Geschichten und passende Bilder)

Ohne Schlüssel läuft das Programm im **Demo-Modus** (Beispielgeschichte + Farbverläufe).
Klicke oben rechts auf **„⚙️ Einstellungen“** und trage ein:

- **Claude-API-Schlüssel:** Konto auf <https://console.anthropic.com> → „API Keys“ → „Create Key“
  (ein paar Euro Guthaben aufladen – ein Video kostet nur wenige Cent).
- **Pexels-API-Schlüssel:** kostenlos auf <https://www.pexels.com/api/>.
- **Stimme:** männlich/weiblich auswählen.

Die Schlüssel werden nur lokal in der Datei `.env` im Projektordner gespeichert (nicht auf GitHub).

### 6. Optional: Musik

Lege lizenzfreie MP3-Dateien in den Ordner `assets/music/` (z. B. aus der YouTube Audio Library
oder von Pixabay Music). Pro Video wird zufällig ein Titel gewählt, leise gemischt und ausgeblendet.

---

## 🛠️ Anpassen für Fortgeschrittene

Alle Einstellungen stehen in `tiktok_generator/config.py`:

| Was? | Einstellung |
|---|---|
| Schriftgröße / Position der Untertitel | `font_size`, `caption_y` |
| Wörter pro Untertitel | `words_per_caption` |
| Eigene Schriftart | `.ttf`-Datei in `assets/fonts/` legen |
| Sprechtempo | `TTS_RATE` in `.env`, z. B. `+15%` |
| Musiklautstärke | `MUSIC_VOLUME` in `.env` |
| Stil der Geschichten | `SYSTEM_PROMPT` in `tiktok_generator/story.py` |
| Anderer Port | `PORT=9000` in `.env` |

Kommandozeile (optional, im aktivierten `.venv`):
`python main.py "Thema" --seconds 45 --count 3`

### Ideen für später

- [ ] KI-generierte Bilder statt Stock-Fotos
- [ ] Übergänge zwischen den Szenen (Überblenden)
- [ ] Hook-Text groß oben in den ersten 3 Sekunden
- [ ] Mehrere Themen auf einmal aus einer Liste
- [ ] Automatisch jeden Tag ein Video erzeugen

---

## 📁 Aufbau des Projekts

```
start.bat / start.command / start.sh  ← Doppelklick zum Starten
app.py                     ← Webserver (Browser-Oberfläche)
templates/index.html       ← Aussehen der Oberfläche
main.py                    ← Kommandozeilen-Version (optional)
tiktok_generator/
  pipeline.py              ← steuert die 6 Schritte + Fortschritt
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
| „Python wurde nicht gefunden“ | Python installieren, bei Windows das Häkchen „Add to PATH“ setzen, dann neu starten |
| macOS: „kann nicht geöffnet werden“ | Rechtsklick auf `start.command` → „Öffnen“ → „Öffnen“ bestätigen |
| macOS: „keine Berechtigung“ | Terminal im Ordner öffnen und einmal `chmod +x start.command start.sh` eingeben |
| Browser öffnet sich nicht | <http://127.0.0.1:8765> selbst eingeben |
| „Address already in use“ | Das Programm läuft schon in einem anderen Fenster – das andere schließen |
| Installation schlägt fehl | Internetverbindung prüfen; Ordner `.venv` löschen und neu starten |
| Video ohne Ton | keine Verbindung zum Microsoft-Sprachdienst – Internet prüfen |
| Fehlermeldung „Schlüssel ungültig“ | in den Einstellungen den Claude-Schlüssel neu eintragen |
| Video zu kurz/lang | `TTS_RATE` in `.env` ändern; im Demo-Modus ist die Länge nur ungefähr |
| Nur Farbverläufe | `PEXELS_API_KEY` fehlt oder ist falsch |

## ⚖️ Hinweise

- Nutze nur Musik und Material, für das du die Rechte hast. Pexels-Inhalte sind frei nutzbar.
- TikTok verlangt, dass KI-generierte Inhalte als solche gekennzeichnet werden
  (beim Hochladen „KI-generierter Inhalt“ aktivieren).
