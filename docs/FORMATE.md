# Formate, Gestaltung, Serien und Qualitätskontrolle

## Funktionsstatus (ehrlich)

| Funktion | Status |
|---|---|
| 5 neue Formate + Fakten-Doku (Skript, Kulissen, Grafiken, Musik, Sprechweise, Untertitel) | ✅ funktioniert, je Format ein Testvideo erstellt und Bild für Bild geprüft |
| Kostenloser Skript-Generator für alle Rätsel-Formate | ✅ funktioniert (500 Imposter-Rätsel automatisch auf Lösbarkeit geprüft) |
| Serien (Figuren, Regeln, Cliffhanger, Vorschau, keine Wiederholungen) | ✅ funktioniert (100 Imposter-Folgen ohne Wiederholung, Vorschau wird in der nächsten Folge eingehalten) |
| Gezeichnete Kulissen, Kamera-Look, Grafiken, sichere Zonen | ✅ funktioniert |
| 4 Untertitelstile, Schlüsselwort-Hervorhebung, wortgenaues Timing | ✅ funktioniert |
| Musik je Format (selbst komponiert), Soundeffekte, Ducking, Limiter | ✅ funktioniert (gemessen: Musik 18 dB unter der Stimme, keine Übersteuerung) |
| Qualitätskontrolle vor/nach Export mit Auto-Korrektur | ✅ funktioniert |
| Weboberfläche (Formate, Probehören, Serien, Szenenvorschau, Kosten, QC-Bericht) | ✅ funktioniert (iPhone-Ansicht im Browser getestet) |
| **Stimmen** (Microsoft Edge TTS) inkl. Figurenstimmen | ⚠️ eingebaut, aber in der Entwicklungsumgebung **nicht erreichbar** – bei dir mit Internet zu testen. Ohne Verbindung: stummer Testmodus |
| **Pexels-Stockvideos** | ⚠️ eingebaut, in der Entwicklungsumgebung nicht erreichbar |
| **Claude-Skripte für die neuen Formate** (eigene Idee, Seriengedächtnis) | ⚠️ eingebaut, aber **noch nie mit echtem Schlüssel gelaufen** (kostenpflichtig – nur nach deiner Zustimmung testen) |
| Kostenpflichtige KI-Videomodelle (Seedance usw.) | 🔒 nicht integriert – wartet auf deine Zustimmung |
| Windows | ⚠️ Code ist plattformunabhängig geschrieben; getestet wurde unter Linux (siehe unten) |

## Die Formate im Detail

| Format | Ablauf | Bildstil | Musik / Sprechweise / Untertitel |
|---|---|---|---|
| Finde den Imposter | Hook → Vorfall mit Uhrzeit → je eine Aussage pro Figur (eigene Stimme) → Hinweis → Countdown 3-2-1 → Auflösung → Vorschau | Innenraum je Schauplatz, Figurenleiste mit hervorgehobenem Sprecher, Sprechblasen | Spannung · spannend · TikTok |
| Mysteriöse Überwachungskamera | Hook → Kameraaufnahmen mit Uhrzeit → Hinweis → veränderte Aufnahme → Countdown → Auflösung mit Markierungskreis → Cliffhanger | Kamera-Look (grünliches Schwarzweiß, Rauschen, Zeilen, REC, laufende Uhr), feste Kamera mit Detail-Zoom | Überwachung · Mystery · Mystery |
| Du entscheidest | Hook → Lage → Gefahr → 2–3 Optionen (Karten) → Aufruf „A, B oder C in die Kommentare“; Folgefolge beginnt mit der gewählten Option | Wüste / Schneesturm / Insel, wechselnde Bildausschnitte mit Requisiten | Abenteuer · spannend · TikTok |
| Unmöglicher Kriminalfall | Hook → Fall → 3 Verdächtige (Aussagen) → Beweise → Countdown → Auflösung | Ermittlungswand mit Zetteln und roten Fäden, Beweiszettel, Täter-Markierung | Detektiv · ruhig · Klar mit Hintergrund |
| Das unendliche Level | Hook → „LEVEL n“ → Ort/Atmosphäre → Regeln (alte + neue) → Ereignis → Cliffhanger „Level n+1“ | endlose Gänge/Schwimmbad/Parkhaus, langsames Vorwärtsgleiten | Unheimlich · Mystery · Mystery |
| Fakten-Doku | wie bisher (Recherche + Faktencheck mit Claude) | Stockvideos oder passende Kulisse | Doku · normal · TikTok |

**Kostenloser Generator – Grenzen:** Die Inhalte werden aus geprüften Bausteinen kombiniert (z. B. 4 Schauplätze ×
6 Vorfälle × 4 Hinweisarten × wechselnde Figuren beim Imposter). Das reicht für 100+ unterschiedliche Imposter-Folgen.
Beim Kriminalfall gibt es 6 Grundfälle (mit wechselnden Namen) – für viele verschiedene Fälle und für **deine eigene
Idee** braucht es Claude.

## Gestaltung

- 1080 × 1920, 30 fps, H.264 + AAC, Standardlänge 40 s (wählbar 30–60 s)
- Einstieg: Hook-Titel ab dem ersten Bild, Akzent-Sound, kurzer Hook-Satz (≤ 12 Wörter, geprüft)
- spätestens alle ~3 Sekunden ein Schnitt bzw. neuer Bildausschnitt, dazu Grafikwechsel je Szene
- **sichere Zonen:** Grafiken im Bereich x 6–84 %, y 9–55 %; Untertitel bei 63 % Höhe, links der Like-Leiste
- ruhige Effekte: dezentes Aufhellen (statt grellem Blitz) und leichtes Wackeln nur bei Hook und Auflösung

## Ton

- Erzählerstimme wählbar (10 deutsche Stimmen inkl. AT/CH) + Sprechweise (normal, spannend, Mystery, ruhig) – probehören in der App
- Figuren in Rätseln bekommen eigene, zum Geschlecht passende Stimmen
- Musik wird je Format selbst komponiert (Spannung, Überwachung, Abenteuer, Detektiv, Unheimlich, Doku) – keine Lizenzfragen.
  Eigene Musik mit Nutzungsrechten: `assets/music/<stil>/`
- Ducking (Musik ~11 dB leiser beim Sprechen), Stimme auf einheitliche Lautheit, Limiter bei −1 dBFS
- Soundeffekte: Hinweis-Ton, Countdown-Ticks im Takt der Anzeige, Entscheidungs-Pop, Auflösungs-Akkord, Kamera-Störung

## Serien

- Anlegen in der App (Serienmodus) oder per Kommandozeile `--series <ID>`; gespeichert in `data/series/` (lokal)
- gespeichert werden: Figuren (feste Namen und Rollen), feste Tatsachen (z. B. Level-Regeln), offene Cliffhanger,
  Zusammenfassungen aller Folgen, Zustand des Generators
- jede neue Folge: gleiche Besetzung (beim Imposter ersetzt ein Neuzugang den letzten Täter), angekündigter Vorfall
  bzw. angekündigtes Level wird umgesetzt, Cliffhanger werden aufgelöst, keine Wiederholungen, Vorschau auf die nächste Folge
- mit Claude: der bisherige Verlauf (letzte 10 Folgen, Figuren, Regeln, offene Fragen, bisherige Täter) geht in jede neue Folge ein

## Qualitätskontrolle

| Prüfung | Wie | Automatische Korrektur |
|---|---|---|
| Alle Szenen vorhanden? | leere Szenen, fehlende Bilder | leere Szenen entfernen |
| Passt das Bild zum Text? | Kulissen entstehen aus Szenentyp + Schauplatz; Stock nur per Suchbegriff (ohne Bild-KI nur grob prüfbar) | fehlende Suchbegriffe ergänzen |
| Stimme und Untertitel synchron? | Wortzeitstempel geordnet und innerhalb ihrer Szene | – |
| Musik nicht zu laut? | Abstand Stimme–Musik gemessen (Ziel ≥ 12 dB) | Ducking |
| Rätsel logisch lösbar? | genau ein Täter aus der Besetzung, der auch spricht; Hinweis vor der Auflösung; Countdown | Countdown ergänzen, Täter in der Auflösung nennen, sonst Skript neu erzeugen |
| Wiederholungen? | doppelte Sätze, gleiche Satzanfänge, Serien-Wiederholungen | doppelte Sätze entfernen |
| Einstieg interessant? | Hook-Länge, Frage/Zahl, Hook-Titel, Akzent-Sound | Hook-Titel und Sound ergänzen |
| MP4 vollständig? | komplette Datei dekodiert, Dauer, Auflösung, Tonspur, schwarze Bilder | einmal neu rendern |

## Neue Abhängigkeiten

Keine. Alle neuen Funktionen nutzen die bereits vorhandenen Pakete (MoviePy, NumPy, Pillow, edge-tts, Flask).

## Getestet

- je Format ein vollständiges Video (30–41 s), Einzelbilder aller Szenentypen angesehen, Qualitätskontrolle bestanden
- Weboberfläche mit iPhone-14-Emulation: Format wählen, Musik probehören, Serie anlegen, Szenen planen, Video erstellen,
  herunterladen, nächste Folge planen – ohne Seitenfehler
- Kostenschutz: ohne Zustimmung kein Planen/Rendern mit Claude (Server antwortet 402)
- **nicht getestet:** echte Stimmen, Pexels, Claude-Skripte (in der Entwicklungsumgebung gesperrt bzw. kostenpflichtig) und Windows selbst
