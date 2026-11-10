# 🎬 KI-Faktenvideos für TikTok

Du gibst nur eine Frage ein – zum Beispiel
**„Was würde passieren, wenn die Erde 5 Sekunden aufhört, sich zu drehen?“** – und bekommst ein
fertiges 9:16-MP4 (30–60 s), bedienbar direkt vom **iPhone**.

| Baustein | So wird es gemacht | Kosten |
|---|---|---|
| 🔎 Recherche & Faktencheck | Claude sucht im Web, prüft Zahlen, sammelt Quellen | ┐ |
| ✍️ Skript mit starkem Hook | Claude schreibt nur aus den geprüften Fakten: Hook → Spannung → Wendung → Pointe | ┘ ca. 0,20–0,50 $ |
| 🗣️ Natürliche deutsche KI-Stimme | Microsoft „Florian/Seraphina Multilingual“, Hook langsamer gesprochen | 0 $ |
| 🎥 Bewegte Videoszenen | Hochkant-Stockvideos (Pexels) + Kamerafahrten · **Hybrid:** echte KI-Szenen für Hook & Höhepunkte (🔒 nach Freigabe) | 0 $ (Hybrid ca. 0,31–0,37 $) |
| ✂️ Dynamischer Schnitt | kurze Einstellungen (≤ 3 s), Zoom-Schläge, Schwenks, Lichtblitz + Wackeln bei Schock-Momenten | 0 $ |
| 💬 Wortgenaue Untertitel | aktuelles Wort gelb, Schlüsselwort pink, „Pop“-Animation, Hook-Titel oben | 0 $ |
| 🔊 Soundeffekte | Whoosh, Impact, Boom, Riser, Tick – selbst erzeugt, ohne Lizenzprobleme | 0 $ |
| 🎵 Musik | eigene MP3s oder automatisch erzeugter Doku-Klangteppich | 0 $ |

**Kostenschutz:** Die App zeigt vor jedem Video die voraussichtlichen Kosten an. Wenn etwas Geld
kostet, startet sie erst, nachdem du ausdrücklich zugestimmt hast – auch der Server prüft das.
Kostenpflichtige KI-Videomodelle sind sichtbar, aber gesperrt (🔒), bis du sie freigibst.
Es wird **nichts automatisch veröffentlicht**. Du lädst das Video selbst bei TikTok hoch.

👉 Vergleich der KI-Videomodelle, Kosten pro 45-s-Video und pro Monat: [docs/KI-VIDEOMODELLE.md](docs/KI-VIDEOMODELLE.md)

### Die drei Modi für Videoszenen

| Modus | Was passiert | Kosten der Szenen |
|---|---|---|
| **Nur Stockvideos** | alle Shots aus kostenlosen Pexels-Videos | 0 $ |
| **Hybrid-Vorschau** | wie oben, aber die geplanten KI-Momente (Hook, Schock, Wendung) sind im Video mit „KI-SZENE · VORSCHAU“ markiert – so siehst du vorab, wo später KI-Szenen kommen | 0 $ |
| **Hybrid mit KI-Modell** 🔒 | die 1–4 wichtigsten Momente werden echte KI-Videoszenen (je ca. 4 s), der Rest Stockvideos | ca. 0,31–0,37 $ (3 KI-Szenen, Seedance 1.5 Pro) – wird erst nach deiner Zustimmung eingebaut |

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

1. Frage eingeben oder einen Vorschlag antippen.
2. Länge wählen (30–60 s).
3. „Faktencheck mit Websuche“ an lassen (empfohlen).
4. Videoszenen: **Nur Stockvideos** oder **Hybrid-Vorschau** (beide kostenlos). Bei Hybrid die Zahl der KI-Szenen wählen.
5. Kosten prüfen und bei Bedarf **Zustimmung anhaken**.
6. **„✨ Video erstellen“** antippen. Der Fortschritt wird live angezeigt.
   Du kannst das iPhone dabei sperren: Beim Öffnen läuft die Anzeige weiter.
7. Fertig: Video ansehen, **„⬇️ MP4 herunterladen“**, Beschreibung mit Hashtags kopieren, Quellen ansehen.

**Video in die Fotos-App speichern:** Nach dem Herunterladen die **Dateien-App** öffnen →
„Downloads“ → Video öffnen → **Teilen → „Video sichern“**. Dann kannst du es in TikTok hochladen.

### 6. Einmalig: Schlüssel eintragen (⚙️ Einstellungen, geht auch vom iPhone)

| Schlüssel | Wofür | Woher | Kosten |
|---|---|---|---|
| **Claude** | Recherche, Faktencheck, Skript zu deinem Thema | <https://console.anthropic.com> → API Keys | ca. 0,20–0,50 $ pro Video |
| **Pexels** | echte, bewegte Hochkant-Videos | <https://www.pexels.com/api/> | kostenlos |

Ohne Claude-Schlüssel läuft ein **kostenloser Testmodus** mit einem fertigen Demo-Skript (Erdrotation).
Die Schlüssel werden nur lokal in der Datei `.env` gespeichert, nie auf GitHub.

**Tipp:** Lege in der Anthropic-Konsole ein **monatliches Ausgabelimit** fest (z. B. 5 $). Dann können nie
höhere Kosten entstehen.

### 7. Optional: eigene Musik

Lizenzfreie MP3s in den Ordner `assets/music/` legen. Ohne eigene Musik erzeugt das Programm einen
spannungsvollen Doku-Klangteppich.

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

Kommandozeile (optional): `python main.py "Frage" --seconds 45` (`--no-factcheck`, `--demo`, `--mode preview`, `--ai-moments 3`)

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
  visuals.py               ← ③ Bildquelle: Stock, Hybrid-Vorschau, KI-Anbieter (nach Freigabe)
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
