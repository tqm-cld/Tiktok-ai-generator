# 🎬 KI-Video-Studio für TikTok

Format wählen, optional eine Idee eingeben, Szenen ansehen, Video erstellen – fertig ist ein
**9:16-MP4 (1080 × 1920, 30–60 s)** mit Stimme, Musik, Soundeffekten, Grafiken und wortgenauen Untertiteln.
Bedienbar am PC und vom **iPhone**.

## Die Formate

| Format | Was passiert | Serie |
|---|---|---|
| 🕵️ **Finde den Imposter** | 3–4 Figuren mit Alibis, ein versteckter Hinweis widerspricht genau einer Aussage, Countdown, logische Auflösung | ✅ |
| 📹 **Mysteriöse Überwachungskamera** | fiktive Kameraaufnahmen (REC, Zeitstempel), eine subtile Veränderung, Auflösung mit Markierung | ✅ |
| 🧭 **Du entscheidest** | Survival-Story mit 2–3 Optionen – die Zuschauer stimmen in den Kommentaren ab, die nächste Folge setzt die Wahl fort | ✅ |
| 🔍 **Unmöglicher Kriminalfall** | Verdächtige, Beweise (Fair Play), Countdown, nachvollziehbare Lösung | ✅ |
| 🚪 **Das unendliche Level** | Mystery-Serie mit Leveln, Regeln, wiederkehrenden Figuren und Cliffhangern | ✅ |
| 🌍 **Fakten-Doku** | faktengeprüftes Wissensvideo mit Quellen (Claude + Websuche) | – |

Jedes Format hat eigene Dramaturgie, Kulissen, Grafiken, Musik, Sprechweise und Untertitelstil.
**Serien:** Figuren, Regeln, Hinweise und offene Cliffhanger werden gespeichert; jede Folge baut darauf auf,
löst Cliffhanger auf, erzeugt eine Vorschau auf die nächste Folge und wiederholt sich nicht (100 Imposter-Folgen getestet).

👉 Alle Details, Funktionsstatus und Grenzen: **[docs/FORMATE.md](docs/FORMATE.md)**

## Was kostet was?

| Baustein | Lösung | Kosten |
|---|---|---|
| Skripte (alle Formate) | eingebauter Generator – geprüfte Bausteine, offline | **0 $** |
| Skripte zu deiner eigenen Idee | Claude (optional, Schlüssel nötig) | ca. 0,01–0,15 $ (Fakten mit Websuche 0,18–0,47 $) |
| Stimmen (Erzähler + Figuren) | Microsoft Edge TTS | 0 $ (Internet nötig) |
| Kulissen & Grafiken | lokal gezeichnet | 0 $ |
| Stockvideos | Pexels (optional) | 0 $ |
| Musik & Soundeffekte | lokal komponiert, lizenzfrei | 0 $ |
| Echte KI-Videoszenen | z. B. Seedance – 🔒 erst nach deiner Zustimmung | ca. 0,31–0,37 $ |

**Kostenschutz:** Vor jedem kostenpflichtigen Schritt (auch beim Planen) zeigt die App die Kosten und startet
erst nach deiner Zustimmung – der Server prüft das zusätzlich. Monatsbudget in den Einstellungen.
Es wird **nichts automatisch veröffentlicht**.

👉 KI-Videomodelle im Vergleich: [docs/KI-VIDEOMODELLE.md](docs/KI-VIDEOMODELLE.md)

---

## ☁️ Online nutzen – nur mit dem iPhone (empfohlen)

Kostenlos mit GitHub Codespaces (laut GitHub 60 Stunden pro Monat gratis), Einrichtung komplett im iPhone-Safari:
👉 **[docs/IPHONE-HOSTING.md](docs/IPHONE-HOSTING.md)**

## 🚀 Auf dem eigenen Computer starten (ohne Python-Befehle)

### 1. Einmalig: Python installieren

- **Windows:** <https://www.python.org/downloads/> → Installer öffnen → **Häkchen „Add python.exe to PATH“** → „Install Now“.
- **macOS:** <https://www.python.org/downloads/> → Installer durchklicken.

FFmpeg musst du nicht extra installieren, es wird automatisch mitgeliefert.

### 2. Einmalig: Projekt herunterladen

Auf GitHub den richtigen Branch wählen → grüner Knopf **„Code“ → „Download ZIP“** → entpacken.

### 3. Auf dem Computer starten

| System | So startest du |
|---|---|
| **Windows** | Doppelklick auf **`start.bat`** |
| **macOS** | beim ersten Mal **Rechtsklick auf `start.command` → „Öffnen“**, danach reicht ein Doppelklick |
| **Linux** | `start.sh` |

Beim ersten Start wird alles automatisch installiert. Das dauert 1–3 Minuten.
Fragt Windows oder macOS, ob **eingehende Verbindungen** erlaubt werden sollen, klicke auf
**„Zulassen“** (nur „Private Netzwerke“). Sonst kann das iPhone den Computer nicht erreichen.

Danach siehst du ein schwarzes Fenster mit Adresse, **Zugangscode** und **QR-Code**. Das Fenster muss offen bleiben,
solange du die App nutzt. Der Computer muss eingeschaltet bleiben, denn dort wird das Video berechnet.

### 4. Vom iPhone steuern 📱

1. iPhone und Computer müssen **im selben WLAN** sein.
2. **iPhone-Kamera öffnen** und auf den QR-Code im schwarzen Fenster halten → Link antippen.
   Du bist dann automatisch angemeldet. Alternativ die angezeigte Adresse (z. B. `http://192.168.1.23:8765`)
   in Safari eintippen und den 6-stelligen Zugangscode eingeben.
3. **Als App auf den Home-Bildschirm legen:** In Safari unten auf **Teilen** (□↑) →
   **„Zum Home-Bildschirm“**. Danach startest du die App mit einem Tipp auf das Symbol.

### 5. Video erstellen

1. **Format** antippen (z. B. „Finde den Imposter“).
2. Optional eine **eigene Idee** eingeben (wird mit Claude-Schlüssel umgesetzt).
3. Optional **Serienmodus** an → Serie wählen oder neu anlegen (bei „Du entscheidest“: gewonnene Option A/B/C wählen).
4. **Länge** (Standard 40 s), **Stimme** + **Sprechweise** (▶ probehören), **Musikstil** (▶ probehören), **Untertitelstil** wählen.
   Format-passende Voreinstellungen werden automatisch gesetzt.
5. **„👁 Szenen planen“**: zeigt alle geplanten Szenen und die Qualitätsprüfung des Skripts.
6. Kosten prüfen und bei Bedarf **Zustimmung anhaken** (im kostenlosen Modus nicht nötig).
7. **„✨ Video erstellen“**. Der Fortschritt wird live angezeigt; du kannst das iPhone dabei sperren.
8. Fertig: Video ansehen, **„⬇️ MP4 herunterladen“**, Qualitätsbericht und Vorschau auf die nächste Folge ansehen,
   **„▶ Nächste Folge planen“**.

**Video in die Fotos-App speichern:** Nach dem Herunterladen die **Dateien-App** öffnen →
„Downloads“ → Video öffnen → **Teilen → „Video sichern“**. Dann kannst du es in TikTok hochladen.

### 6. Einmalig: Schlüssel eintragen (⚙️ Einstellungen, geht auch vom iPhone)

| Schlüssel | Wofür | Woher | Kosten |
|---|---|---|---|
| **Claude** | Skripte zu deiner eigenen Idee; Fakten-Recherche | <https://console.anthropic.com> → API Keys | ca. 0,01–0,50 $ pro Video (je nach Format und Modell) |
| **Pexels** | echte, bewegte Hochkant-Videos | <https://www.pexels.com/api/> | kostenlos |

Ohne Claude-Schlüssel schreibt der **kostenlose Generator** die Skripte aller Rätsel-Formate (abwechslungsreich,
logisch geprüft, auch als Serie); deine eigene Idee fließt dann noch nicht ein. Die Fakten-Doku nutzt ohne
Schlüssel ein Demo-Skript (Erdrotation).
Die Schlüssel werden nur lokal in der Datei `.env` gespeichert, nie auf GitHub.

**Tipp:** Lege in der Anthropic-Konsole ein **monatliches Ausgabelimit** fest (z. B. 5 $). Dann können nie
höhere Kosten entstehen.

### 7. Optional: eigene Musik

Die App komponiert für jedes Format passende Musik selbst (keine Lizenzfragen). Eigene Musik **mit geklärten
Nutzungsrechten** kann in `assets/music/<stil>/` liegen (z. B. `assets/music/spannung/titel.mp3`) und hat dann Vorrang.
Stile: `spannung`, `ueberwachung`, `abenteuer`, `detektiv`, `level`, `doku`.

---

## 🔐 Sicherheit

- Vom iPhone aus kommt nur hinein, wer den **Zugangscode** kennt (steht in `.env` als `ACCESS_CODE`).
  Am Computer selbst wird kein Code benötigt.
- Die App ist nur in deinem **eigenen WLAN** erreichbar, nicht im Internet.
- In fremden WLANs (Café, Hotel) solltest du den iPhone-Zugriff abschalten: `PHONE_ACCESS=0` in `.env`.
- Neuen Code erzeugen: Zeile `ACCESS_CODE=…` aus `.env` löschen und neu starten.
- **Unterwegs (außerhalb des WLANs):** möglich mit der kostenlosen App *Tailscale* auf Computer und iPhone.
  Das ist noch nicht eingebaut, auf Wunsch richten wir es gemeinsam ein.

---

## 🛟 Häufige Probleme

| Problem | Lösung |
|---|---|
| „Python wurde nicht gefunden“ | Python installieren (Häkchen „Add to PATH“), dann neu starten |
| macOS: „kann nicht geöffnet werden“ | Rechtsklick auf `start.command` → „Öffnen“ → „Öffnen“ |
| iPhone: Seite lädt nicht | gleiches WLAN? Firewall-Abfrage mit „Zulassen“ beantwortet? Fenster noch offen? |
| iPhone: „Zugangscode fehlt“ | QR-Code erneut scannen oder Code aus dem schwarzen Fenster eingeben |
| „Address already in use“ | Die App läuft schon in einem anderen Fenster – das andere schließen |
| Video ohne Stimme | Internetverbindung des Computers prüfen (die Stimme kommt von Microsoft) |
| Nur generierte Hintergründe | Pexels-Schlüssel in den Einstellungen eintragen |
| „Schlüssel ungültig“ | Claude-Schlüssel in den Einstellungen neu eintragen |
| Installation schlägt fehl | Internet prüfen, Ordner `.venv` löschen, neu starten |

---

## 💰 Kosten im Griff

- **Vor jedem Video:** Kostenschätzung + Zustimmungs-Häkchen (der Server prüft das zusätzlich).
- **Nach jedem Video:** die tatsächlichen Kosten (aus den Verbrauchsangaben der API berechnet).
- **Monatsbudget** (⚙️ Einstellungen, Standard 10 $): Ist es erreicht, startet kein kostenpflichtiges Video mehr.
  Alle Ausgaben stehen lokal in `data/ausgaben.json`.
- **Claude-Modell wählbar:** Opus 5.5 (Standard, gründlichster Faktencheck), Sonnet 5.5 (halb so teuer) oder
  Haiku 5.5 (am günstigsten). Das Skript ist der größte Kostenblock pro Video.
- Einmal erzeugte KI-Clips werden gespeichert und nie doppelt bezahlt.

## 🛠️ Für Fortgeschrittene

| Was | Wo |
|---|---|
| Untertitel-Größe/Position | `font_size`, `caption_y` in `tiktok_generator/config.py` |
| Tempo des Schnitts | `MAX_CUT_SECONDS` in `tiktok_generator/video.py` |
| Helligkeit der Szenen | `DARKEN` in `tiktok_generator/video.py` |
| Sprechtempo / Stimme | `TTS_RATE`, `TTS_VOICE` in `.env` |
| Stil der Skripte | `SCRIPT_SYSTEM` / `RESEARCH_SYSTEM` in `tiktok_generator/story.py` |
| Preise / Modelle | `tiktok_generator/costs.py` |
| KI-Videoanbieter einbinden | `AI_PROVIDERS` in `tiktok_generator/visuals.py` |
| Monatsbudget / Claude-Modell | `MONTHLY_BUDGET_USD`, `CLAUDE_MODEL` in `.env` (oder ⚙️ Einstellungen) |
| Port | `PORT=9000` in `.env` |

Kommandozeile (optional): `python main.py "Idee" --format imposter --seconds 40`
(`--format imposter|cctv|entscheidung|krimi|level|fakten`, `--series <ID>`, `--choice A`, `--subtitles mystery`,
`--music spannung`, `--no-factcheck`, `--demo`, `--mode preview`, `--ai-moments 3`)

### Projektaufbau

```
start.bat / start.command / start.sh   ← Doppelklick zum Starten
app.py                     ← Webserver, iPhone-Zugang, Kostenfreigabe
templates/                 ← Oberfläche (index.html, login.html)
static/                    ← App-Symbol fürs iPhone
docs/KI-VIDEOMODELLE.md    ← Modellvergleich & Kosten
docs/IPHONE-HOSTING.md     ← Kostenlos online nutzen mit GitHub Codespaces (iPhone-Anleitung)
.devcontainer/             ← Startkonfiguration für Codespaces (installiert & startet die App automatisch)
deploy/huggingface/        ← Dockerfile für Hugging Face (nur mit kostenpflichtigem PRO-Abo)
tiktok_generator/
  pipeline.py              ← steuert alle Schritte + Fortschritt
  story.py                 ← ① Recherche, Faktencheck, Skript (Claude)
  voice.py                 ← ② KI-Stimme + Wortzeitstempel
  formats.py               ← die 6 Formate (Dramaturgie, Musik, Stimme, Untertitel, Bildstil)
  offline.py               ← kostenloser Skript-Generator für alle Formate (inkl. Serien)
  series.py                ← Serien: Figuren, Regeln, Cliffhanger, Folgen
  scenes.py                ← gezeichnete Kulissen je Format
  overlays.py              ← Grafiken: Aussagen, Hinweise, Countdown, Auswahl, Regeln, Kamera-HUD
  audio.py                 ← Stimmen, Musikstile, Ducking, Normalisierung, Limiter
  qc.py                    ← Qualitätskontrolle vor und nach dem Export
  visuals.py               ← ③ Bildquelle: Kulisse, Stock, Hybrid-Vorschau, KI-Anbieter (nach Freigabe)
  ledger.py                ←    Ausgabenbuch + Monatsbudget
  media.py                 ←    Pexels-Suche / generierte Hintergründe
  video.py                 ← ④ dynamischer Schnitt, Hook-Titel, Export
  subtitles.py             ← ⑤ wortgenaue animierte Untertitel
  sfx.py                   ← ⑥ Soundeffekte + Doku-Musik
  music.py                 ←    eigene Musik
  costs.py                 ←    Preiskatalog & Kostenschätzung
```

## ⚖️ Hinweise

- TikTok verlangt, dass KI-generierte Inhalte gekennzeichnet werden. Beim Hochladen „KI-generierter Inhalt“ aktivieren.
- Die Quellen werden in der App angezeigt. Prüfe vor dem Veröffentlichen kurz, ob die Aussagen stimmen.
  Ein automatischer Faktencheck ist sehr gut, aber nicht unfehlbar.
- Nutze nur Musik, für die du die Rechte hast. Pexels-Videos sind frei nutzbar.
