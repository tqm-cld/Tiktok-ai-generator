# Projektstand (10. November 2026)

## Was fertig ist

- **Web-App** (`app.py`, Flask): Frage eingeben → fertiges 9:16-MP4 (30–60 s) ansehen und herunterladen,
  mit Fortschrittsanzeige, Galerie und Einstellungen. Fürs iPhone optimiert (Home-Bildschirm-App).
- **Pipeline** (`tiktok_generator/`):
  - Recherche mit Faktencheck (Claude + Websuche) und Skript mit Hook
  - KI-Stimme (Microsoft Edge TTS, kostenlos)
  - Stockvideos (Pexels, kostenlos)
  - dynamischer Schnitt, wortgenaue Untertitel, Soundeffekte und Musik
- **Kostenschutz:**
  - Kostenschätzung und Zustimmung vor jedem Video, zusätzlich vom Server geprüft
  - echte Claude-Kosten werden erfasst, mit Ausgabenbuch und Monatsbudget
  - Claude-Modell in den Einstellungen wählbar
- **Hybrid-Modus vorbereitet:**
  - Das Skript markiert 1–4 KI-Momente.
  - Eine kostenlose „Hybrid-Vorschau“ markiert diese Momente im Video.
  - Die Schnittstelle für KI-Videoanbieter steht (`AI_PROVIDERS` in `visuals.py`), aber **es ist noch kein Modell eingebaut**.
- **Hosting:**
  - GitHub Codespaces (kostenlos, `.devcontainer/`), Anleitung in `docs/IPHONE-HOSTING.md`
  - Hugging Face nur mit PRO-Abo (`deploy/huggingface/`)

## Offene Aufgaben

1. **Kostenloser Test am echten iPhone** über Codespaces (noch nicht durchgeführt).
2. **Stimme und Pexels-Videos** unter echten Bedingungen prüfen. In der bisherigen Testumgebung waren diese Dienste gesperrt.
3. **Claude-Schlüssel eintragen** ⚠️ *kostenpflichtig, ca. 0,03–0,50 $ pro Video, vorher Zustimmung*: erst dann wird dein Prompt wirklich umgesetzt.
4. **Seedance 1.5 Pro einbauen** ⚠️ *kostenpflichtig, ca. 0,31–0,37 $ pro Video, erst nach Zustimmung*:
   Konto bei BytePlus, ein Testclip (ca. 0,10–0,13 $), dann die Preise in `costs.py` korrigieren
   (siehe `docs/KI-VIDEOMODELLE.md`).
5. Optional: Zugriff von unterwegs (z. B. Tailscale), wenn die App auf dem eigenen PC läuft.

## Auf Windows starten

1. **Python 3.10+** von <https://www.python.org/downloads/> installieren und das Häkchen **„Add python.exe to PATH“** setzen.
2. **Git** von <https://git-scm.com> installieren.
3. Projekt holen, in PowerShell oder der Eingabeaufforderung:
   ```
   git clone https://github.com/tqm-cld/Tiktok-ai-generator.git
   cd Tiktok-ai-generator
   git checkout claude/tiktok-ai-video-generator-m6ldsj
   ```
4. **Doppelklick auf `start.bat`**:
   - Beim ersten Start wird alles automatisch installiert (1–3 Minuten).
   - Danach öffnet sich der Browser mit <http://127.0.0.1:8765>.
   - Fürs iPhone im selben WLAN: den QR-Code im schwarzen Fenster scannen.
   - Die Windows-Firewall-Abfrage mit „Zulassen“ (private Netzwerke) beantworten.
5. **Mit Claude Code weiterarbeiten:** im Projektordner `claude` starten und z. B. sagen:
   *„Lies PROJEKTSTAND.md und README.md, dann machen wir mit Aufgabe 1 weiter.“*

Schlüssel (Claude, Pexels) gehören in die Datei `.env` oder in ⚙️ Einstellungen. Sie werden **nie** auf GitHub
hochgeladen (`.gitignore`). Weitere Details stehen in `README.md`.
