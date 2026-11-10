"""Weboberfläche für den TikTok-KI-Generator.

Starten: Doppelklick auf start.bat (Windows) bzw. start.command (macOS) oder ./start.sh (Linux).
Danach öffnet sich der Browser automatisch auf http://127.0.0.1:8765
"""

import logging
import os
import threading
import traceback
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from tiktok_generator.config import PROJECT_ROOT, Config
from tiktok_generator.pipeline import make_video
from tiktok_generator.story import StoryError

HOST = "127.0.0.1"   # nur auf diesem Computer erreichbar
PORT = int(os.getenv("PORT", "8765"))
ENV_FILE = PROJECT_ROOT / ".env"
SETTING_KEYS = ["ANTHROPIC_API_KEY", "PEXELS_API_KEY", "TTS_VOICE"]

app = Flask(__name__)

# Videos werden nacheinander erstellt (Rendern braucht viel Rechenleistung).
executor = ThreadPoolExecutor(max_workers=1)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


# ---------------------------------------------------------------- Hilfsfunktionen

def _update(job_id: str, **fields):
    with jobs_lock:
        jobs[job_id].update(fields)


def _video_info(path: Path) -> dict:
    caption_file = path.with_suffix(".txt")
    caption = caption_file.read_text(encoding="utf-8").strip() if caption_file.exists() else ""
    return {
        "name": path.name,
        "title": caption.split(" #")[0] if caption else path.stem,
        "caption": caption,
        "url": f"/videos/{path.name}",
        "download_url": f"/videos/{path.name}?download=1",
        "created": path.stat().st_mtime,
    }


def _run_job(job_id: str, topic: str, seconds: int):
    def progress(percent: int, message: str):
        _update(job_id, progress=percent, message=message)

    _update(job_id, status="running", message="Starte …")
    try:
        result = make_video(topic, Config(), seconds=seconds, progress=progress)
        _update(job_id, status="done", progress=100, message="Fertig!",
                video=_video_info(result.video_path), demo=result.demo,
                duration=round(result.duration), warnings=result.warnings)
    except StoryError as e:
        _update(job_id, status="error", message=str(e))
    except Exception as e:  # unerwarteter Fehler → Details in die Konsole
        traceback.print_exc()
        _update(job_id, status="error", message=f"❌ Unerwarteter Fehler: {type(e).__name__}: {e}")


def _read_env() -> dict[str, str]:
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


def _write_env(updates: dict[str, str]):
    """Ändert nur die genannten Zeilen der .env-Datei, alles andere bleibt erhalten."""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    done = set()
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if key in updates and not line.lstrip().startswith("#"):
            lines[i] = f"{key}={updates[key]}"
            done.add(key)
    lines += [f"{k}={v}" for k, v in updates.items() if k not in done]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in updates.items():
        os.environ[k] = v  # sofort wirksam, ohne Neustart


# ---------------------------------------------------------------- Seiten & API

@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()
    try:
        seconds = int(data.get("seconds", 45))
    except (TypeError, ValueError):
        seconds = 45
    if not topic:
        return jsonify(error="Bitte gib ein Videothema ein."), 400
    if len(topic) > 300:
        return jsonify(error="Das Thema ist zu lang (max. 300 Zeichen)."), 400
    seconds = max(30, min(60, seconds))

    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {"id": job_id, "status": "queued", "progress": 0,
                        "message": "Wartet auf den Start …", "topic": topic, "seconds": seconds}
    executor.submit(_run_job, job_id, topic, seconds)
    return jsonify(jobs[job_id]), 202


@app.get("/api/jobs/<job_id>")
def job_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            abort(404)
        return jsonify(dict(job))


@app.get("/api/videos")
def list_videos():
    cfg = Config()
    files = sorted(cfg.output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonify([_video_info(p) for p in files[:24]])


@app.get("/videos/<path:name>")
def serve_video(name: str):
    return send_from_directory(Config().output_dir, name,
                               as_attachment=request.args.get("download") == "1")


@app.get("/api/settings")
def get_settings():
    env = {**_read_env(), **{k: os.environ.get(k, "") for k in SETTING_KEYS if os.environ.get(k)}}
    return jsonify({
        "has_anthropic_key": bool(env.get("ANTHROPIC_API_KEY")),
        "has_pexels_key": bool(env.get("PEXELS_API_KEY")),
        "voice": env.get("TTS_VOICE") or Config().voice,
        "music_count": len([p for p in Config().music_dir.glob("*")
                            if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}]),
    })


@app.post("/api/settings")
def save_settings():
    data = request.get_json(silent=True) or {}
    updates = {}
    for key in SETTING_KEYS:
        value = str(data.get(key, "")).strip()
        if value:  # leere Felder = unverändert lassen
            if any(c in value for c in "\r\n"):
                return jsonify(error="Ungültiger Wert."), 400
            updates[key] = value
    if updates:
        _write_env(updates)
    return get_settings()


def main():
    url = f"http://{HOST}:{PORT}"
    print("\n" + "=" * 56)
    print("  🎬 TikTok-KI-Generator läuft!")
    print(f"  Öffne im Browser:  {url}")
    print("  Zum Beenden dieses Fenster schließen (oder Strg+C).")
    print("=" * 56 + "\n")
    if os.getenv("NO_BROWSER") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # keine technischen Meldungen im Fenster
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
