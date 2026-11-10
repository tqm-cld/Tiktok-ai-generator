# 📱 Die App kostenlos online nutzen – nur mit dem iPhone

**Lösung: GitHub Codespaces.** Das ist ein Rechner in der Cloud, den GitHub dir kostenlos zur Verfügung stellt.
Dein Code liegt schon auf GitHub, du brauchst kein neues Konto.

| | |
|---|---|
| **Kosten** | 0 $. Laut GitHub sind für private Konten **120 Kernstunden pro Monat gratis**, das sind **60 Stunden** auf dem 2-Kern-Rechner, plus 15 GB Speicher. |
| **Reicht das?** | Ein Video braucht ca. 2–4 Minuten Rechenzeit. Bei 3 Videos am Tag und ca. 45 Minuten Laufzeit pro Tag sind das ca. 23 Stunden im Monat. |
| **Privat?** | Ja. Deine App-Adresse funktioniert nur, wenn du bei GitHub angemeldet bist. |
| **Einschränkung** | Der Cloud-Rechner läuft nicht dauerhaft. Du startest ihn vor der Nutzung mit einem Tipp (ca. 30–60 Sekunden). |

> Die GitHub-Menüs können leicht anders heißen als hier beschrieben.

---

## Teil A – Einmalige Einrichtung (ca. 10 Minuten)

### Schritt 1: Kostenschutz prüfen (1 Minute)

1. In Safari <https://github.com/settings/billing> öffnen und bei GitHub anmelden.
2. Hier siehst du, wie viel vom Gratis-Kontingent verbraucht ist.
3. Ist **keine Zahlungsmethode** hinterlegt, kann GitHub dir nichts berechnen: Wenn das Kontingent aufgebraucht
   ist, stoppen Codespaces einfach. Falls du eine Karte hinterlegt hast, setze bei
   **Budgets** für **Codespaces** ein Budget von **0 $**, mit der Option, die Nutzung beim Erreichen zu stoppen.

### Schritt 2: Codespace anlegen (1 Minute + 3–5 Minuten Wartezeit)

1. In Safari diesen Link öffnen: <https://codespaces.new/tqm-cld/Tiktok-ai-generator?quickstart=1>
2. Falls eine Auswahl erscheint:
   - **Branch:** `claude/tiktok-ai-video-generator-m6ldsj`
   - **Machine type:** **2-core** (nicht größer, größere Rechner verbrauchen das Kontingent schneller)
3. **Create codespace** antippen.
4. Ein Editor (Visual Studio Code im Browser) öffnet sich. Beim **ersten Mal** werden 3–5 Minuten lang alle Pakete
   installiert. Danach erscheint unten im Terminal:
   **„✅ App gestartet auf Port 8765“**.

### Schritt 3: App-Link öffnen und speichern

1. Im Editor unten den Reiter **Ports** öffnen.
   Auf dem iPhone, falls er nicht zu sehen ist: oben links **☰** → **View/Ansicht** → **Open View…** → `Ports`.
2. In der Zeile **„KI-Videos App (8765)“** auf das **Globus-Symbol** („Open in Browser“) tippen.
3. Es öffnet sich deine App unter einer Adresse wie
   `https://dein-codespace-name-8765.app.github.dev`.
   Falls GitHub fragt, ob du den Port öffnen möchtest: **Continue** antippen.
4. **Als App speichern:** unten **Teilen** (□↑) → **Zum Home-Bildschirm** → **Hinzufügen**.

⚠️ Die Sichtbarkeit des Ports muss **Private** bleiben (so ist es voreingestellt). Dann kommt nur rein, wer mit deinem
GitHub-Konto angemeldet ist. **Niemals auf „Public“ stellen.**

### Schritt 4: Erstes kostenloses Testvideo

1. Prompt eingeben, z. B. *„Was würde passieren, wenn die Erde 5 Sekunden aufhört, sich zu drehen?“*
2. **Videoszenen:** „Nur Stockvideos“ oder „Hybrid-Vorschau“.
3. **Kosten prüfen:** Es muss **„kostenlos“** dastehen. Ohne Claude-Schlüssel ist das automatisch so.
4. **✨ Video erstellen**. Das dauert ca. 2–4 Minuten.
5. **⬇️ MP4 herunterladen** → **Dateien-App** → Downloads → Video öffnen → **Teilen → „Video sichern“**.

Im kostenlosen Test wird das fertige **Demo-Skript zur Erdrotation** verwendet. Dein Prompt wird also noch nicht
umgesetzt. Getestet wird die ganze Technik: Stimme, Stockvideos, Schnitt, Untertitel, Musik, Download.

**Optional, aber kostenlos:** ⚙️ Einstellungen → **Pexels-Schlüssel** eintragen (<https://www.pexels.com/api/>).
Dann gibt es echte, bewegte Stockvideos statt generierter Hintergründe.

---

## Teil B – Jedes weitere Mal (ca. 1 Minute)

1. <https://github.com/codespaces> öffnen → deinen Codespace antippen. Er startet in ca. 30–60 Sekunden, und die
   App startet automatisch mit.
2. Sobald der Editor geladen ist: das **App-Symbol auf dem Home-Bildschirm** öffnen.
3. **Nach der Nutzung** (spart Gratis-Stunden): <https://github.com/codespaces> → **⋯** neben dem Codespace →
   **Stop codespace**. Vergisst du das, stoppt er nach 30 Minuten ohne Nutzung von selbst.

---

## Gut zu wissen

| Thema | Was passiert |
|---|---|
| **Videos** | bleiben im Codespace gespeichert (Galerie „Meine Videos“), solange der Codespace existiert |
| **Ungenutzt** | Nach 30 Tagen ohne Nutzung löscht GitHub den Codespace. Dann einfach Schritt 2 wiederholen. |
| **Einstellungen** | Schlüssel aus ⚙️ Einstellungen bleiben im Codespace gespeichert, aber **nicht** auf GitHub |
| **Updates** | Wenn ich die App verbessere: neuen Codespace anlegen (Schritt 2) und den alten löschen |
| **Fehler** | Im Editor im Terminal `cat /tmp/tiktok-app.log` eingeben und mir einen Screenshot schicken. Neustart der App: `bash .devcontainer/start-app.sh` |
| **Verbrauch** | <https://github.com/settings/billing> |

---

## Teil C – Echte Videos zu deinem Prompt (kostenpflichtig, erst nach Rücksprache)

**Jeder dieser Schritte kostet Geld, deshalb besprechen wir ihn vorher.**

1. **Claude (Recherche + Skript zu deinem Prompt):** ca. 0,03–0,50 $ pro Video, je nach Claude-Modell.
   Konto auf <https://console.anthropic.com>, Guthaben aufladen, **Ausgabenlimit setzen**, dann in ⚙️ Einstellungen
   den Schlüssel eintragen.
2. **Hybrid mit echten KI-Szenen (Seedance 1.5 Pro):** ca. 0,31–0,37 $ pro Video zusätzlich. Wird erst eingebaut,
   wenn du zustimmst (siehe [KI-VIDEOMODELLE.md](KI-VIDEOMODELLE.md)).
