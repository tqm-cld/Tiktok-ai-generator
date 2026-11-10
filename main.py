"""Startpunkt des Programms.

Beispiele:
    python main.py "Eine gruselige Geschichte über einen Leuchtturm"
    python main.py "Ein witziger Fakt über Katzen" --count 3
    python main.py --demo          (ohne API-Schlüssel testen)
"""

import argparse
import re
from datetime import datetime

from tiktok_generator.config import Config
from tiktok_generator.media import fetch_media
from tiktok_generator.story import demo_story, generate_story
from tiktok_generator.video import build_video
from tiktok_generator.voice import synthesize


def slugify(text: str) -> str:
    text = text.lower()
    for a, b in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:40] or "video"


def make_one_video(topic: str, cfg: Config, demo: bool = False):
    print("\n① Geschichte schreiben …")
    story = demo_story() if demo else generate_story(topic, cfg)
    print(f"  ✓ „{story.title}“ – {len(story.scenes)} Szenen, {len(story.full_text.split())} Wörter")

    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{slugify(story.title)}"
    work_dir = cfg.cache_dir / run_id

    print("② Stimme erzeugen …")
    voices = []
    for i, scene in enumerate(story.scenes):
        voices.append(synthesize(scene.text, work_dir / f"voice_{i:02d}.mp3", cfg))
    print(f"  ✓ Gesamtlänge Sprache: {sum(v.duration for v in voices):.1f}s")

    print("③ Bilder/Videos suchen …")
    media = []
    for scene in story.scenes:
        path = fetch_media(scene.visual_query, cfg, work_dir / "media")
        media.append(path)
        print(f"  • {scene.visual_query:35s} → {path.name}")

    print("④–⑥ Untertitel, Musik und Video zusammenbauen …")
    out_path = cfg.output_dir / f"{run_id}.mp4"
    build_video(voices, media, out_path, cfg)

    # Beschreibung + Hashtags zum Kopieren für TikTok
    caption = f"{story.title} " + " ".join(f"#{h.lstrip('#')}" for h in story.hashtags)
    out_path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    out_path.with_suffix(".json").write_text(story.model_dump_json(indent=2), encoding="utf-8")

    print(f"\n✅ Fertig: {out_path}")
    print(f"   TikTok-Beschreibung: {caption}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Erstellt automatisch TikTok-Kurzvideos mit KI.")
    parser.add_argument("topic", nargs="?", default="Eine mysteriöse Kurzgeschichte mit überraschendem Ende",
                        help="Worum soll die Geschichte gehen?")
    parser.add_argument("--count", type=int, default=1, help="Wie viele Videos erstellt werden sollen")
    parser.add_argument("--demo", action="store_true", help="Demo-Geschichte verwenden (kein API-Schlüssel nötig)")
    parser.add_argument("--voice", help="Andere Stimme, z.B. de-DE-KatjaNeural")
    args = parser.parse_args()

    cfg = Config()
    if args.voice:
        cfg.voice = args.voice

    for n in range(args.count):
        if args.count > 1:
            print(f"\n===== Video {n + 1} von {args.count} =====")
        make_one_video(args.topic, cfg, demo=args.demo)


if __name__ == "__main__":
    main()
