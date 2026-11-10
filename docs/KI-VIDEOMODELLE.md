# KI-Videomodelle im Vergleich (Stand: November 2026)

> ⚠️ Die Preise stammen aus öffentlichen Preisübersichten. Diese widersprechen sich teilweise,
> weil Anbieter Preise oft ändern und je nach Auflösung, Tonspur und Plattform unterschiedlich abrechnen.
> **Vor einer Freischaltung prüfen wir die Preise noch einmal auf der offiziellen Seite des Anbieters.**
> Alle Preise in US-Dollar.

## Annahmen für „Kosten pro Video“

- Videolänge 45 Sekunden. Die Spalten „100 % KI“ und „Hybrid“ zeigen nur die Videokosten; die Gesamtkosten in der Empfehlung enthalten Skript und ggf. Stimme. Davon werden **alle Szenen** per KI erzeugt (Spalte „100 % KI“)
  oder nur die wichtigsten **40 %**: Hook, Höhepunkt, Wendung (Spalte „Hybrid“). Der Rest kommt
  aus kostenlosen Stockvideos.
- Bezahlt wird immer der ganze Clip (z. B. 5 oder 8 s). Dazu kommen ca. 20 % Reserve für misslungene
  Clips, die neu erzeugt werden müssen.
- Wo möglich **ohne KI-Ton**, denn Stimme, Musik und Soundeffekte macht unser Programm selbst.

## Videomodelle

| Modell | Anbieter | $/Sekunde | Auflösung | Qualität | 45 s, 100 % KI | Hybrid (40 %) | Bemerkung |
|---|---|---|---|---|---|---|---|
| **Testmodus** (Stock + Kamerafahrten) | Pexels | 0 | bis 1080p | ★★☆☆☆ | **0 $** | 0 $ | ✅ freigeschaltet, passt nicht immer exakt |
| LTX-2.3 Fast | fal.ai | ~0,05 | 1080p | ★★★☆☆ | 2,25–2,70 $ | 1,00–1,20 $ | schnell, schwächer bei komplexen Szenen |
| MiniMax Hailuo 2.3 Fast | MiniMax | 0,19 $/6-s-Clip | 768p | ★★★☆☆ | 1,52–1,82 $ | 0,57–0,68 $ | offizieller Preis; als „legacy“ gelistet |
| **Google Veo 3.1 Lite** | Google | 0,03 (ohne Ton) / 0,05 (mit Ton) | 720p | ★★★★☆ | **1,44–1,73 $** | **0,72–0,86 $** | bestes Preis-Leistungs-Verhältnis |
| Kling 2.6 Pro | fal.ai | ~0,07 | 1080p | ★★★★☆ | 3,15–3,78 $ | 1,40–1,68 $ | sehr flüssige Bewegungen |
| Google Veo 3.1 Fast | Google | 0,10 | 720p | ★★★★★ | 4,80–5,76 $ | 2,40–2,88 $ | sehr realistisch, starke Physik |
| Wan 3.0 | fal.ai | ~0,10 | 720p | ★★★★☆ | 4,50–5,40 $ | 2,00–2,40 $ | Open Source, auch selbst hostbar |
| Kling 3 Pro | fal.ai | ~0,11 | 1080p | ★★★★★ | 5,04–6,05 $ | 2,24–2,69 $ | Top-Qualität |
| Seedance 2.0 Fast | fal.ai | ~0,24 | 720p | ★★★★★ | 10,80–12,96 $ | 4,80–5,76 $ | exzellent, aber teuer |
| ~~Sora 2~~ | OpenAI | – | – | – | – | – | API laut Berichten im Sept. 2026 abgeschaltet |

**Hinweis zu Veo:** Laut einer Quelle sollten die Vorschau-Versionen in der Gemini-API im Oktober 2026
auslaufen. Möglicher Nachfolger ist „Gemini Omni Flash“. Vor der Integration prüfen wir, was aktuell angeboten wird.

## Weitere Kosten pro Video

| Baustein | Lösung | Kosten |
|---|---|---|
| Recherche + Faktencheck + Skript | Claude (mit Websuche) | ca. 0,18–0,49 $ |
| Skript ohne Faktencheck | Claude | ca. 0,06–0,15 $ |
| KI-Stimme Standard | Microsoft Edge TTS („Florian/Seraphina Multilingual“) | 0 $ |
| KI-Stimme Premium (emotionaler) | ElevenLabs v3 (~0,08 $ pro 1000 Zeichen) | ca. 0,05 $ |
| Untertitel, Schnitt, Soundeffekte, Musik | lokal auf deinem Computer | 0 $ |

## Empfehlung

| Stufe | Zusammensetzung | ca. Kosten pro 45-s-Video |
|---|---|---|
| **1. Testmodus (jetzt)** | Claude-Skript mit Faktencheck + Edge-Stimme + Stockvideos | **0,20–0,50 $** |
| **2. Hybrid (Empfehlung)** | wie 1, plus Veo 3.1 Lite für Hook & Höhepunkte, optional ElevenLabs | **0,90–1,42 $** |
| 3. Voll-KI | alle Szenen mit Veo 3.1 Lite | 1,62–2,22 $ |
| 4. Premium | alle Szenen mit Kling 3 Pro oder Veo 3.1 Fast + ElevenLabs | 5,03–6,60 $ |

Kostenpflichtige Videomodelle sind im Programm sichtbar, aber **gesperrt (🔒)**. Sie werden erst eingebaut,
wenn du zustimmst. Auch danach zeigt die App vor jedem Video die geschätzten Kosten und startet erst,
wenn du sie bestätigt hast.

## Quellen der Preisangaben

- invideo: AI Video Model Pricing (Aug. 2026) – https://invideo.io/blog/ai-video-model-pricing/
- Teamday: fal.ai Pricing (Nov. 2026) – https://www.teamday.ai/blog/fal-ai-pricing-2026
- Atlas Cloud: Cheapest AI Video Generation APIs 2026 – https://www.atlascloud.ai/blog/tips/cheapest-ai-video-generation-api-2026
- MiniMax: Pricing Overview (offiziell) – https://platform.minimax.io/docs/guides/pricing-video
- BenchLM: Veo 3.1 API Pricing – https://benchlm.ai/media-pricing/veo
- 8frame: Veo 3.1 Price Comparison 2026 – https://www.8frame.co/blog/veo-3-1-price-comparison-2026
- Tech Insider: Veo 3.1 vs Kling 3.0 vs Gemini Omni – https://tech-insider.org/best-ai-video-generator-2026/
- AIReiter: Kling 4.0 API Pricing on fal – https://aireiter.com/blog/kling-4-0-api-pricing-fal-cost-vs-seedance-vidu
- UsagePricing: ElevenLabs v4 launch / TTS price cut (Okt. 2026) – https://www.usagepricing.com/blueprint/activity/elevenlabs-2026-10-05-v4-launch-tts-price-cut
