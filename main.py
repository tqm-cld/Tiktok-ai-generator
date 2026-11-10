"""Kommandozeilen-Version (für Fortgeschrittene). Normalerweise reicht die Weboberfläche: start.bat / start.command / start.sh

Beispiele:
    python main.py "Eine gruselige Geschichte über einen Leuchtturm"
    python main.py "Ein witziger Fakt über Katzen" --seconds 30 --count 3
    python main.py --demo          (ohne API-Schlüssel testen)
"""

import argparse

from tiktok_generator.config import Config
from tiktok_generator.pipeline import make_video
from tiktok_generator.story import StoryError


def main():
    parser = argparse.ArgumentParser(description="Erstellt automatisch TikTok-Kurzvideos mit KI.")
    parser.add_argument("topic", nargs="?", default="Was würde passieren, wenn die Erde 5 Sekunden aufhört, sich zu drehen?",
                        help="Worum soll die Geschichte gehen?")
    parser.add_argument("--seconds", type=int, default=45, help="Gewünschte Länge (30-60 Sekunden)")
    parser.add_argument("--count", type=int, default=1, help="Wie viele Videos erstellt werden sollen")
    parser.add_argument("--demo", action="store_true", help="Demo-Geschichte verwenden (kein API-Schlüssel nötig)")
    parser.add_argument("--voice", help="Andere Stimme, z.B. de-DE-SeraphinaMultilingualNeural")
    parser.add_argument("--no-factcheck", action="store_true", help="Ohne Websuche/Faktencheck (günstiger)")
    parser.add_argument("--mode", default="stock", help="stock | preview (Hybrid-Vorschau) | freigegebenes KI-Modell")
    parser.add_argument("--ai-moments", type=int, default=3, help="Anzahl KI-Szenen im Hybrid-Modus (1-4)")
    args = parser.parse_args()

    cfg = Config()
    if args.voice:
        cfg.voice = args.voice
    seconds = max(cfg.min_seconds, min(cfg.max_seconds, args.seconds))

    for n in range(args.count):
        if args.count > 1:
            print(f"\n===== Video {n + 1} von {args.count} =====")
        try:
            result = make_video(args.topic, cfg, seconds=seconds, demo=args.demo,
                                fact_check=not args.no_factcheck, mode=args.mode,
                                ai_moments=args.ai_moments)
        except StoryError as e:
            raise SystemExit(str(e))
        print(f"\n✅ Fertig: {result.video_path}  ({result.duration:.0f} s)")
        print(f"   TikTok-Beschreibung: {result.caption}")


if __name__ == "__main__":
    main()
