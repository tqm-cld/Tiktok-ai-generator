# 📱 Die App online stellen und am iPhone nutzen (kostenlos)

Am Ende hast du einen **privaten Link** (z. B. `https://deinname-tiktok-generator.hf.space`). Dort gibst du einen
Prompt ein und lädst das fertige MP4 herunter. Dein Computer muss dafür **nicht** laufen.

**Hosting:** [Hugging Face Spaces](https://huggingface.co/spaces), kostenlose Stufe „CPU basic“
(2 CPU-Kerne, 16 GB RAM). Es wird **keine Kreditkarte** benötigt. Alles geht im iPhone-Safari.

> Die Menüs bei Hugging Face können leicht anders heißen als hier beschrieben. Sie ändern ihre Seite gelegentlich.

---

## Teil 1 – Kostenloser Test (ohne Claude, ohne KI-Videos)

Im kostenlosen Test verwendet die App das fertige **Demo-Skript zur Erdrotation**. Dein Prompt wird also noch nicht
umgesetzt. Getestet wird die ganze Technik: Stimme, Stockvideos, Schnitt, Untertitel, Musik, Download.
**Kosten: 0 $.**

### Schritt 1: Hugging-Face-Konto anlegen (2 Minuten)

1. In Safari <https://huggingface.co/join> öffnen.
2. E-Mail und Passwort eingeben → Benutzername wählen → **Create account**.
3. Die Bestätigungs-E-Mail öffnen und den Link antippen.

### Schritt 2: Space anlegen (1 Minute)

1. <https://huggingface.co/new-space> öffnen.
2. Ausfüllen:
   - **Space name:** `tiktok-generator`
   - **Select the Space SDK:** **Docker** → Vorlage **Blank**
   - **Space hardware:** **CPU basic · FREE** (nichts anderes wählen, alles andere kostet Geld)
   - **Visibility:** **Private** (nur du kannst den Space sehen)
3. **Create Space** antippen.

### Schritt 3: Bauanleitung einfügen (2 Minuten)

1. In einem neuen Safari-Tab diese Datei öffnen:
   <https://raw.githubusercontent.com/tqm-cld/Tiktok-ai-generator/claude/tiktok-ai-video-generator-m6ldsj/deploy/huggingface/Dockerfile>
2. Lange auf den Text drücken → **Alles auswählen** → **Kopieren**.
3. Zurück zum Space-Tab → oben **Files** → **+ Add file** → **Create a new file**.
4. Als Dateiname genau `Dockerfile` eintippen (großes D, keine Endung).
5. Ins große Textfeld tippen → **Einsetzen**.
6. Ganz unten **Commit new file to main** antippen.

Der Space beginnt jetzt zu bauen. Oben steht **Building**, die erste Erstellung dauert ca. 3–6 Minuten.

### Schritt 4: Zugangscode festlegen (1 Minute)

Damit niemand außer dir Videos erzeugen kann, braucht die App zusätzlich einen Zugangscode.

1. Im Space oben **Settings** antippen.
2. Nach unten zu **Variables and secrets** → **New secret**.
3. **Name:** `ACCESS_CODE`, **Value:** ein langes Passwort, das du dir merkst
   (z. B. `Leuchtturm-Banane-2026-Zebra`; Tipp: im iPhone-Passwortmanager speichern).
4. **Save**. Der Space startet danach neu.

**Optional, aber kostenlos und empfehlenswert:** Ein zweites Secret `PEXELS_API_KEY` mit deinem kostenlosen
Pexels-Schlüssel (<https://www.pexels.com/api/>) anlegen. Dann bekommst du echte, bewegte Stockvideos statt
generierter Hintergründe.

⚠️ **`ANTHROPIC_API_KEY` jetzt noch NICHT eintragen.** Das wäre der erste kostenpflichtige Schritt (siehe Teil 2).

### Schritt 5: Warten, bis „Running“ angezeigt wird

- Oben neben dem Namen steht der Status. Er wechselt von **Building** zu **Running**.
- Falls **Build error** oder **Runtime error** erscheint: auf **Logs** tippen, einen Screenshot machen und ihn mir schicken.

### Schritt 6: Deinen privaten Link öffnen

1. Im Space oben rechts auf **⋮** (drei Punkte) → **Embed this Space** tippen.
2. Bei **Direct URL** steht dein Link, z. B. `https://deinname-tiktok-generator.hf.space`. Diesen Link öffnen.
   (Nicht die Ansicht innerhalb der Hugging-Face-Seite benutzen. Dort kann Safari die Anmeldung nicht speichern.)
3. Den Zugangscode aus Schritt 4 eingeben → **Anmelden**.
4. **Als App speichern:** unten auf **Teilen** (□↑) → **Zum Home-Bildschirm** → **Hinzufügen**.

### Schritt 7: Erstes Testvideo

1. Prompt eingeben, z. B. *„Was würde passieren, wenn die Erde 5 Sekunden aufhört, sich zu drehen?“*
2. **Videoszenen:** „Nur Stockvideos“ oder „Hybrid-Vorschau“.
3. **Kosten prüfen:** Es muss **„kostenlos“** dastehen. Ohne Claude-Schlüssel ist das automatisch so.
4. **✨ Video erstellen**. Das dauert ca. 2–5 Minuten, du kannst das iPhone dabei sperren.
5. **⬇️ MP4 herunterladen** → **Dateien-App** öffnen → Downloads → Video öffnen → **Teilen → „Video sichern“**.

✅ Wenn das klappt, läuft die ganze Technik online.

---

## Gut zu wissen

| Thema | Was passiert |
|---|---|
| **Ruhezustand** | Nach 48 Stunden ohne Nutzung schläft der kostenlose Space ein. Beim nächsten Öffnen wacht er in ca. 1–3 Minuten auf. |
| **Videos speichern** | Videos werden bei einem Neustart des Space gelöscht. Deshalb jedes Video **gleich herunterladen**. |
| **Einstellungen in der App** | Schlüssel immer über **Hugging-Face-Secrets** eintragen, nicht über ⚙️ in der App. Was dort gespeichert wird, ist nach einem Neustart weg. |
| **Ausgabenbuch / Monatsbudget** | Wird bei einem Neustart zurückgesetzt. Bei kostenpflichtigen Diensten deshalb **zusätzlich immer ein Limit im Konto des Anbieters** setzen. |
| **Updates** | Wenn ich die App auf GitHub verbessere: Space → **Settings** → **Factory rebuild**. |
| **Kosten bei Hugging Face** | Die Stufe „CPU basic“ ist kostenlos. Kostenpflichtig wären nur bessere Hardware oder dauerhafter Speicher. Das brauchen wir nicht. |

---

## Teil 2 – Echte Videos zu deinem Prompt (kostenpflichtig, erst nach Rücksprache)

Wenn der kostenlose Test klappt, sind das die nächsten Schritte. **Jeder davon kostet Geld, deshalb besprechen wir ihn
vorher.**

1. **Claude (Recherche + Skript zu deinem Prompt):** ca. 0,03–0,50 $ pro Video, je nach Claude-Modell.
   Konto auf <https://console.anthropic.com>, Guthaben aufladen, **Ausgabenlimit setzen**, dann Secret
   `ANTHROPIC_API_KEY` anlegen. Optional `CLAUDE_MODEL` (z. B. `claude-sonnet-5-5`) und `MONTHLY_BUDGET_USD`.
2. **Hybrid mit echten KI-Szenen (Seedance 1.5 Pro):** ca. 0,31–0,37 $ pro Video zusätzlich. Wird erst eingebaut,
   wenn du zustimmst (siehe [KI-VIDEOMODELLE.md](KI-VIDEOMODELLE.md)).
