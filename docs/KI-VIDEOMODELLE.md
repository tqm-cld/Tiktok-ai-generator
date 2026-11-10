# KI-Videomodelle für den Hybrid-Modus (Stand: November 2026)

> ⚠️ Die Preise stammen aus öffentlichen Preisübersichten und Anbieterseiten. Sie widersprechen sich teilweise,
> weil Anbieter Preise häufig ändern und je nach Auflösung, Ton und Region unterschiedlich abrechnen.
> **Vor der Freischaltung prüfen wir den Preis des gewählten Modells noch einmal beim Anbieter.**
> Alle Preise in US-Dollar. Die Qualitätssterne sind eine grobe Einschätzung aus Testberichten, nicht selbst gemessen.

## So funktioniert der Hybrid-Modus

Ein 45-s-Video besteht aus ca. 9–11 Shots. Nur die **wichtigsten Momente** werden als echte KI-Videoszene
erzeugt – je ca. 4 Sekunden:

1. **Hook** (immer)
2. **Schock-Moment / Höhepunkt**
3. **Wendung**
4. (optional) ein weiterer Höhepunkt

Alle anderen Shots kommen aus **kostenlosen Pexels-Stockvideos**. Die Anzahl der KI-Szenen (1–4) stellst du in der
App mit einem Regler ein. Einmal erzeugte KI-Clips werden gespeichert und nie doppelt bezahlt.

## Worauf es bei kurzen Clips ankommt

Bei 4-s-Momenten zählt nicht nur der Sekundenpreis, sondern auch, **welche Cliplängen** ein Modell anbietet:
Wer nur 6-s- oder 10-s-Clips verkauft, lässt dich pro Moment 2 s umsonst bezahlen.

## Vergleich: Veo 3.1 Lite und günstigere Alternativen

Kosten der KI-Clips für **ein 45-s-Video mit 3 KI-Szenen** (min. = alles klappt beim ersten Versuch,
max. = mit 20 % Reserve für Neuversuche):

| Modell | Anbieter | Preis | bezahlte Cliplänge | 9:16 | Qualität | Einrichtung | **KI-Clips pro Video** |
|---|---|---|---|---|---|---|---|
| **Seedance 1.5 Pro** | BytePlus (ByteDance) | ≈ 0,026 $/s (720p, ohne Ton)¹ | 4 s (frei wählbar) | ja | ★★★★ | mittel | **0,31–0,37 $** |
| Grok Imagine Video 1.5 Lite | xAI | 0,02–0,03 $/s (720p)² | 4 s (1–15 s frei) | zu prüfen | ★★★ | einfach | 0,36–0,43 $ |
| Google Veo 3.1 Lite (Vertex AI) | Google Cloud | 0,03 $/s (720p, ohne Ton) | 4 s (4/6/8 s) | ja | ★★★★ | aufwendig | 0,36–0,43 $ |
| Wan 2.6 Flash (Bild→Video) | Alibaba Cloud | 0,025 $/s (720p, ohne Ton) | 5 s | über Startbild | ★★★ | aufwendig | 0,38–0,45 $ |
| MiniMax Hailuo 2.3 Fast | MiniMax | 0,19 $ pro 6-s-Clip | 6 s (6/10 s) | über Startbild | ★★★ | mittel | 0,57–0,68 $ |
| Google Veo 3.1 Lite (Gemini API) | Google AI Studio | 0,05 $/s (720p, nur mit Ton) | 4 s (4/6/8 s) | ja | ★★★★ | einfach | 0,60–0,72 $ |
| *Zum Vergleich: Kling 2.6 Pro* | fal.ai | ≈ 0,07 $/s | 5 s | ja | ★★★★ | einfach | 1,05–1,26 $ |
| *Zum Vergleich: Veo 3.1 Fast* | Google | 0,10 $/s | 4 s | ja | ★★★★★ | einfach | 1,20–1,44 $ |

¹ Seedance wird nach Tokens abgerechnet (1,20 $ pro 1 Mio. Tokens ohne Ton). Die 0,026 $/s sind meine Umrechnung
für 720p-Hochformat. Der echte Preis wird nach der Integration mit **einem Testclip** gemessen.
² Je nach Quelle 0,02 $/s (480p) bis 0,03 $/s (720p).

## Kosten für ein fertiges 45-Sekunden-Video

Ein fertiges Video setzt sich so zusammen: **Recherche + Faktencheck + Skript (Claude)** + KI-Clips. Stimme,
Stockvideos, Musik, Soundeffekte, Untertitel und Schnitt sind kostenlos.

| Claude-Modell (in den Einstellungen wählbar) | Skript | + Seedance 1.5 Pro (3 KI-Szenen) | + Veo 3.1 Lite Vertex (3 KI-Szenen) |
|---|---|---|---|
| Opus 5.5 (Standard, gründlichster Faktencheck) | 0,18–0,47 $ | **0,49–0,85 $** | 0,54–0,90 $ |
| Sonnet 5.5 (halb so teuer) | 0,10–0,26 $ | **0,41–0,63 $** | 0,46–0,69 $ |
| Haiku 5.5 (am günstigsten, schwächerer Faktencheck) | 0,03–0,05 $ | **0,35–0,43 $** | 0,39–0,48 $ |

Die Skriptkosten sind eine Schätzung. Nach jedem Video zeigt die App die **tatsächlichen** Claude-Kosten, die aus
den Verbrauchsangaben der API berechnet werden, und führt ein Ausgabenbuch.

**Noch günstiger:** Mit nur 2 KI-Szenen (Hook + Höhepunkt) kosten die Clips mit Seedance nur 0,21–0,25 $.

### Monatskosten bei 1–3 Videos pro Tag

| Variante | pro Video | 1 Video/Tag (30) | 3 Videos/Tag (90) |
|---|---|---|---|
| Nur Stockvideos + Opus-Skript | 0,18–0,47 $ | 5–14 $ | 16–42 $ |
| **Hybrid: Seedance + Opus** | 0,49–0,85 $ | 15–26 $ | 44–77 $ |
| **Hybrid: Seedance + Sonnet** | 0,41–0,63 $ | 12–19 $ | 37–57 $ |
| Hybrid: Seedance + Haiku | 0,35–0,43 $ | 11–13 $ | 32–39 $ |

Das **Monatsbudget** in den Einstellungen (Standard 10 $) verhindert, dass mehr ausgegeben wird.
Zusätzlich empfehle ich ein Ausgabenlimit direkt im Konto jedes Anbieters.

## Empfehlung: Seedance 1.5 Pro

**Bestes Preis-Leistungs-Verhältnis für den Hybrid-Modus:**

- günstigster Anbieter mit ★★★★-Qualität: 0,31–0,37 $ für 3 KI-Szenen
- Cliplänge frei wählbar, also keine bezahlten, aber ungenutzten Sekunden
- Hochformat 9:16 direkt per Text-Prompt, kein Startbild nötig

**Zweite Wahl: Veo 3.1 Lite über Vertex AI.** Gleich gute Qualität bei ähnlichem Preis, die Einrichtung des
Google-Cloud-Projekts ist für Anfänger aber deutlich umständlicher. Über die einfache Gemini-API kostet Veo Lite
fast doppelt so viel (nur mit Ton abrechenbar).

**Wenn die Einrichtung möglichst einfach sein soll:** Grok Imagine 1.5 Lite (xAI). Ähnlicher Preis, aber
9:16-Unterstützung und Qualität müssen erst mit einem Testclip geprüft werden.

### Ablauf nach deiner Zustimmung

1. Du legst ein Konto beim gewählten Anbieter an, lädst ein kleines Guthaben auf (z. B. 5 $), setzt dort ein
   Ausgabenlimit und trägst den API-Schlüssel in der App unter ⚙️ Einstellungen ein.
2. Ich baue das Modell als Anbieter in `tiktok_generator/visuals.py` ein (Eintrag in `AI_PROVIDERS`).
3. **Ein einzelner Testclip** (ca. 0,10–0,13 $): echter Preis und Qualität werden geprüft, die Preistabelle
   wird korrigiert.
4. Erst dann ist der Modus in der App auswählbar. Vor jedem Video gilt weiter: Kosten anzeigen → zustimmen → starten.

## Quellen

- Alibaba Cloud Model Studio – Model pricing: https://www.alibabacloud.com/help/en/model-studio/model-pricing
- Alibaba Cloud – wan2.6-i2v-flash: https://www.alibabacloud.com/help/en/model-studio/wan2-6-i2v-flash
- BytePlus ModelArk – Pricing: https://ai.byteplus.com/ark/region:ap-southeast-1/docs/model-pricing
- OpenRouter – Seedance 1.5 Pro: https://openrouter.ai/bytedance/seedance-1-5-pro
- Developers Digest – Video generation API pricing (Okt. 2026): https://www.developersdigest.tech/blog/image-video-generation-api-pricing-2026
- Miraflow – Grok Imagine Video 1.5 Lite: https://miraflow.ai/blog/grok-imagine-video-1-5-lite-explained-pricing-benchmarks-api-2026
- LLM Gateway – Grok Imagine Video 1.5 Lite: https://llmgateway.io/models/grok-imagine-video-1-5-lite
- Screenweaver – AI Video Model Pricing Compared: https://www.screenweaver.ai/blog/ai-video-model-pricing-compared
- CloudZero – Veo 3 pricing 2026: https://www.cloudzero.com/blog/veo-3-pricing/
- Atlas Cloud – Veo 3.1 API Pricing: https://www.atlascloud.ai/blog/tips/veo-3.1-api-pricing
- MiniMax – Pricing Overview: https://platform.minimax.io/docs/guides/pricing-video
- Pollo AI Docs – Hailuo 2.3: https://docs.pollo.ai/m/hailuo/hailuo-2-3.md
- Eden AI – Best AI Video Generation APIs 2026: https://www.edenai.co/post/best-ai-video-generation-apis
- invideo – AI Video Model Pricing (Aug. 2026): https://invideo.io/blog/ai-video-model-pricing/
