"""Weboberfläche für den TikTok-KI-Generator – auch vom iPhone aus bedienbar.

Starten: Doppelklick auf start.bat (Windows) bzw. start.command (macOS) oder ./start.sh (Linux).
- Am Computer öffnet sich der Browser automatisch.
- Am iPhone (im selben WLAN): den QR-Code im schwarzen Fenster mit der Kamera scannen.
  Fremde Geräte brauchen den Zugangscode, der ebenfalls im Fenster steht.
"""

import hmac
import logging
import os
import secrets
import socket
import threading
import traceback
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, abort, jsonify, make_response, redirect, render_template, request, send_from_directory

from tiktok_generator.config import PROJECT_ROOT, Config
from tiktok_generator import ledger
from tiktok_generator.audio import MUSIC_STYLES, VOICE_STYLES, VOICES, generate_music, write_wav
from tiktok_generator.costs import CLAUDE_MODELS, catalog, estimate
from tiktok_generator.formats import FORMATS, get_format, list_formats
from tiktok_generator.pipeline import make_video, plan_story, render_story
from tiktok_generator.series import create_series, list_series, load_series
from tiktok_generator.story import StoryError
from tiktok_generator.subtitles import STYLES as SUB_STYLES
from tiktok_generator.visuals import ProviderNotEnabled, available_modes
from tiktok_generator.voice import reset_tts_state, synthesize

PORT = int(os.getenv("PORT", "8765"))
# PHONE_ACCESS=0 in .env schaltet den Zugriff vom Handy ab (dann nur noch dieser Computer)
PHONE_ACCESS = os.getenv("PHONE_ACCESS", "1") != "0"
HOST = "0.0.0.0" if PHONE_ACCESS else "127.0.0.1"
ENV_FILE = PROJECT_ROOT / ".env"
SETTING_KEYS = ["ANTHROPIC_API_KEY", "PEXELS_API_KEY", "TTS_VOICE", "CLAUDE_MODEL", "MONTHLY_BUDGET_USD"]
COOKIE = "tiktok_access"
PREVIEW_DIR = PROJECT_ROOT / "cache" / "previews"

app = Flask(__name__)

# Videos werden nacheinander erstellt (Rendern braucht viel Rechenleistung).
executor = ThreadPoolExecutor(max_workers=1)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


# ---------------------------------------------------------------- .env lesen/schreiben

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


def _access_code() -> str:
    """6-stelliger Zugangscode für Handys – wird einmal erzeugt und in .env gespeichert."""
    code = os.getenv("ACCESS_CODE") or _read_env().get("ACCESS_CODE")
    if not code:
        code = f"{secrets.randbelow(10**6):06d}"
        _write_env({"ACCESS_CODE": code})
    os.environ["ACCESS_CODE"] = code
    return code


ACCESS_CODE = _access_code()


# ---------------------------------------------------------------- Zugangsschutz

def _is_local() -> bool:
    return request.remote_addr in ("127.0.0.1", "::1")


def _with_cookie(resp):
    resp.set_cookie(COOKIE, ACCESS_CODE, max_age=60 * 60 * 24 * 365, httponly=True, samesite="Lax")
    return resp


@app.before_request
def check_access():
    if _is_local() or request.path in ("/login", "/manifest.webmanifest") or request.path.startswith("/static/"):
        return None
    from_link = request.args.get("code", "")
    code = from_link or request.cookies.get(COOKIE, "")
    if hmac.compare_digest(code.encode(), ACCESS_CODE.encode()):
        # Code aus dem QR-Link → als Cookie merken und die Adresse ohne Code anzeigen
        return _with_cookie(redirect(request.path)) if from_link else None
    if request.path.startswith(("/api/", "/videos/")):
        return jsonify(error="Zugangscode fehlt"), 401
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if hmac.compare_digest(code.encode(), ACCESS_CODE.encode()):
            return _with_cookie(redirect("/"))
        error = "Falscher Code. Er steht im schwarzen Fenster auf deinem Computer bzw. in der Datei .env (ACCESS_CODE)."
    return render_template("login.html", error=error)


# ---------------------------------------------------------------- Videoerstellung

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


PLANS: dict[str, dict] = {}          # geplante Skripte (Szenenvorschau) – werden beim Rendern wiederverwendet
PLANS_LOCK = threading.Lock()


def _render_options(data: dict) -> dict:
    """Gestaltungs-Optionen aus der Anfrage (nur bekannte Werte zulassen)."""
    voice = str(data.get("voice") or "")
    vstyle = str(data.get("voice_style") or "")
    music = str(data.get("music_style") or "")
    subs = str(data.get("subtitle_style") or "")
    return {"voice": voice if voice in {v for v, _, _ in VOICES} else None,
            "voice_style": vstyle if vstyle in VOICE_STYLES else None,
            "music_style": music if music in MUSIC_STYLES else None,
            "subtitle_style": subs if subs in SUB_STYLES else None}


def _story_preview(story, checks) -> dict:
    return {
        "title": story.title, "format": story.format, "episode": story.episode, "series_name": story.series_name,
        "hook_title": story.hook_title, "setting": story.setting, "culprit": story.culprit, "solution": story.solution,
        "choices": story.choices, "next_teaser": story.next_teaser,
        "characters": [{"name": c.name, "role": c.role} for c in story.characters],
        "scenes": [{"kind": s.kind, "speaker": s.speaker, "text": s.text, "on_screen": s.on_screen, "sfx": s.sfx}
                   for s in story.scenes],
        "est_seconds": round(sum(len(s.text.split()) for s in story.scenes) / 2.55),
        "checks": [c.dict() for c in checks], "script_cost_usd": story.script_cost_usd,
    }


def _run_job(job_id: str, params: dict, plan_id: str | None):
    def progress(percent: int, message: str):
        _update(job_id, progress=percent, message=message)

    _update(job_id, status="running", message="Starte …")
    cfg = Config()
    try:
        opts = params["options"]
        if plan_id:
            with PLANS_LOCK:
                plan = PLANS.pop(plan_id, None)
            if not plan:
                raise StoryError("❌ Die Szenenvorschau ist abgelaufen. Bitte neu planen.")
            result = render_story(plan["story"], cfg, progress, params["mode"], params["ai_moments"],
                                  script_checks=plan["checks"], **opts)
        else:
            result = make_video(params["topic"], cfg, seconds=params["seconds"], progress=progress,
                                fact_check=params["fact_check"], mode=params["mode"], ai_moments=params["ai_moments"],
                                fmt=params["format"], series_id=params["series_id"], choice=params["choice"], **opts)
        _update(job_id, status="done", progress=100, message="Fertig!",
                video=_video_info(result.video_path), demo=result.demo,
                duration=round(result.duration), warnings=result.warnings, sources=result.sources,
                cost_usd=result.cost_usd, ai_shots=result.ai_shots, qc=result.qc, qc_summary=result.qc_summary,
                episode=result.episode, series_id=result.series_id, next_teaser=result.next_teaser,
                music=result.music)
    except (StoryError, ProviderNotEnabled) as e:
        _update(job_id, status="error", message=str(e))
    except FileNotFoundError:
        _update(job_id, status="error", message="❌ Die gewählte Serie wurde nicht gefunden.")
    except Exception as e:  # unerwarteter Fehler → Details in die Konsole
        traceback.print_exc()
        _update(job_id, status="error", message=f"❌ Unerwarteter Fehler: {type(e).__name__}: {e}")


def _int(value, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def _parse_request(data: dict) -> dict:
    fmt = str(data.get("format") or "fakten")
    fmt = fmt if fmt in FORMATS else "fakten"
    series_id = str(data.get("series_id") or "") or None
    choice = str(data.get("choice") or "").strip().upper()[:1] or None
    return {
        "topic": str(data.get("topic", "")).strip(), "format": fmt,
        "seconds": _int(data.get("seconds"), get_format(fmt).default_seconds, 30, 60),
        "mode": str(data.get("mode", "stock")),
        "fact_check": data.get("fact_check", True) not in (False, "false", "0", 0) and get_format(fmt).research,
        "ai_moments": _int(data.get("ai_moments"), 3, 1, 4),
        "series_id": series_id, "choice": choice if choice in ("A", "B", "C") else None,
        "options": _render_options(data),
    }


def _estimate_for(p: dict, script_planned: bool = False) -> dict:
    cfg = Config()
    est = estimate(p["seconds"], p["mode"], ai_moments=p["ai_moments"], fact_check=p["fact_check"],
                   has_claude=bool(cfg.anthropic_api_key) and not script_planned, claude_model=cfg.claude_model)
    if script_planned:
        est["items"][0]["label"] = "Skript: bereits geplant (keine weiteren Kosten)"
    elif not cfg.anthropic_api_key:
        est["items"][0]["label"] = "Skript: kostenloser Generator (kein Claude-Schlüssel)"
    est["month"] = ledger.summary(cfg.monthly_budget_usd)
    est["over_budget"] = est["paid"] and est["month"]["spent"] + est["total_max"] > cfg.monthly_budget_usd
    return est


def _series_missing(p: dict):
    """Gibt eine Fehlermeldung zurück, wenn die gewählte Serie nicht existiert."""
    if not p["series_id"]:
        return None
    try:
        load_series(p["series_id"])
        return None
    except (FileNotFoundError, ValueError):
        return jsonify(error="Die gewählte Serie wurde nicht gefunden."), 404


def _cost_gate(data: dict, est: dict):
    """Kostenfreigabe: Ohne ausdrückliche Bestätigung startet nichts, was Geld kostet."""
    if est["paid"] and data.get("confirm_cost") is not True:
        return jsonify(error="Bitte bestätige zuerst die voraussichtlichen Kosten.", estimate=est), 402
    if est["over_budget"]:
        m = est["month"]
        return jsonify(error=f"Das Monatsbudget reicht für dieses Video nicht: {m['spent']:.2f} $ von "
                             f"{m['budget']:.2f} $ verbraucht, dieses Video kostet bis zu {est['total_max']:.2f} $. "
                             "Budget in den Einstellungen erhöhen oder nächsten Monat weitermachen.",
                       estimate=est), 402
    return None


# ---------------------------------------------------------------- Seiten & API

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/manifest.webmanifest")
def manifest():
    resp = make_response(jsonify({
        "name": "TikTok-KI-Generator", "short_name": "KI-Videos", "start_url": "/",
        "display": "standalone", "background_color": "#0b0b12", "theme_color": "#0b0b12",
        "icons": [{"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }))
    resp.mimetype = "application/manifest+json"
    return resp


@app.get("/api/options")
def options():
    """Alles, was die Startseite zur Auswahl braucht."""
    cfg = Config()
    return jsonify({
        "formats": list_formats(),
        "voices": [{"id": v, "name": n} for v, n, _ in VOICES],
        "voice_styles": [{"id": k, "name": v["name"]} for k, v in VOICE_STYLES.items()],
        "music_styles": [{"id": k, "name": v} for k, v in MUSIC_STYLES.items()],
        "subtitle_styles": [{"id": k, "name": v["name"]} for k, v in SUB_STYLES.items()],
        "default_voice": cfg.voice, "has_claude": bool(cfg.anthropic_api_key),
    })


@app.get("/api/models")
def models():
    enabled = available_modes()
    moments = _int(request.args.get("ai_moments"), 3, 1, 4)
    return jsonify([{**m, "integrated": m["key"] in enabled}
                    for m in catalog(ai_moments=moments, claude_model=Config().claude_model)])


@app.post("/api/estimate")
def api_estimate():
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(_estimate_for(_parse_request(data), bool(data.get("plan_id")) and data["plan_id"] in PLANS))
    except KeyError:
        return jsonify(error="Unbekanntes Modell."), 400


@app.post("/api/voice-preview")
def voice_preview():
    data = request.get_json(silent=True) or {}
    opts = _render_options(data)
    cfg = Config()
    voice = opts["voice"] or cfg.voice
    style = VOICE_STYLES.get(opts["voice_style"] or "normal")
    sample = "Einer von ihnen lügt. Hör genau hin – findest du den Fehler, bevor die Zeit abläuft?"
    reset_tts_state()
    target = PREVIEW_DIR / f"voice_{voice}_{opts['voice_style'] or 'normal'}.mp3"
    if not target.exists():
        clip = synthesize(sample, target, cfg, rate=style["rate"], voice=voice, pitch=style["pitch"])
        if clip.silent:
            return jsonify(error="Die Stimme ist gerade nicht erreichbar (keine Internetverbindung zu Microsoft)."), 503
    return jsonify(url=f"/previews/{target.name}")


@app.get("/api/music-preview/<style>")
def music_preview(style: str):
    if style not in MUSIC_STYLES:
        abort(404)
    target = PREVIEW_DIR / f"music_{style}.wav"
    if not target.exists():
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        write_wav(target, generate_music(style, 12.0, seed=11) * 0.8)
    return send_from_directory(PREVIEW_DIR, target.name)


@app.get("/previews/<path:name>")
def previews(name: str):
    return send_from_directory(PREVIEW_DIR, name)


@app.get("/api/series")
def api_series():
    fmt = request.args.get("format")
    items = list_series()
    return jsonify([s for s in items if not fmt or s["format"] == fmt])


@app.post("/api/series")
def api_series_create():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify(error="Bitte gib der Serie einen Namen."), 400
    fmt = str(data.get("format") or "imposter")
    s = create_series(name, fmt if fmt in FORMATS else "imposter", str(data.get("idea", "")))
    return jsonify(next(x for x in list_series() if x["id"] == s["id"])), 201


@app.post("/api/plan")
def api_plan():
    """Skript planen und als Szenenvorschau zurückgeben (wird beim Rendern wiederverwendet)."""
    data = request.get_json(silent=True) or {}
    p = _parse_request(data)
    cfg = Config()
    if p["format"] == "fakten" and not p["topic"]:
        return jsonify(error="Bitte gib eine Frage oder ein Thema ein."), 400
    if len(p["topic"]) > 300:
        return jsonify(error="Die Idee ist zu lang (max. 300 Zeichen)."), 400
    missing = _series_missing(p)
    if missing:
        return missing
    est = _estimate_for({**p, "mode": "stock"})                # Planen kostet nur das Skript
    gate = _cost_gate(data, est)
    if gate:
        return gate
    try:
        story, checks = plan_story(p["format"], p["topic"], cfg, p["seconds"], p["series_id"], p["choice"],
                                   p["fact_check"], p["ai_moments"])
    except StoryError as e:
        return jsonify(error=str(e)), 400
    except FileNotFoundError:
        return jsonify(error="Die gewählte Serie wurde nicht gefunden."), 404
    plan_id = uuid.uuid4().hex[:12]
    with PLANS_LOCK:
        if len(PLANS) > 40:
            PLANS.pop(next(iter(PLANS)))
        PLANS[plan_id] = {"story": story, "checks": checks}
    return jsonify(plan_id=plan_id, **_story_preview(story, checks))


@app.post("/api/jobs")
def create_job():
    data = request.get_json(silent=True) or {}
    p = _parse_request(data)
    plan_id = str(data.get("plan_id") or "") or None
    if plan_id and plan_id not in PLANS:
        return jsonify(error="Die Szenenvorschau ist abgelaufen. Bitte neu planen."), 400
    if not plan_id and p["format"] == "fakten" and not p["topic"]:
        return jsonify(error="Bitte gib eine Frage oder ein Thema ein."), 400
    if len(p["topic"]) > 300:
        return jsonify(error="Das Thema ist zu lang (max. 300 Zeichen)."), 400
    if p["mode"] not in available_modes():
        return jsonify(error="Dieses KI-Videomodell ist noch nicht freigeschaltet. "
                             "Kostenpflichtige Modelle werden erst nach deiner Zustimmung eingebaut."), 400
    missing = _series_missing(p)
    if missing:
        return missing
    est = _estimate_for(p, script_planned=bool(plan_id))
    gate = _cost_gate(data, est)
    if gate:
        return gate

    job_id = uuid.uuid4().hex[:12]
    with jobs_lock:
        jobs[job_id] = {"id": job_id, "status": "queued", "progress": 0, "message": "Wartet auf den Start …",
                        "topic": p["topic"], "seconds": p["seconds"], "format": p["format"], "estimate": est}
    executor.submit(_run_job, job_id, p, plan_id)
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
    files = sorted(Config().output_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonify([_video_info(p) for p in files[:24]])


@app.get("/videos/<path:name>")
def serve_video(name: str):
    return send_from_directory(Config().output_dir, name, as_attachment=request.args.get("download") == "1")


@app.get("/api/settings")
def get_settings():
    env = {**_read_env(), **{k: os.environ[k] for k in SETTING_KEYS if os.environ.get(k)}}
    cfg = Config()
    return jsonify({
        "has_anthropic_key": bool(env.get("ANTHROPIC_API_KEY")),
        "has_pexels_key": bool(env.get("PEXELS_API_KEY")),
        "voice": env.get("TTS_VOICE") or cfg.voice,
        "claude_model": cfg.claude_model,
        "claude_models": [[k, v[0]] for k, v in CLAUDE_MODELS.items()],  # Liste = feste Reihenfolge
        "month": ledger.summary(cfg.monthly_budget_usd),
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
            if key == "CLAUDE_MODEL" and value not in CLAUDE_MODELS:
                return jsonify(error="Unbekanntes Claude-Modell."), 400
            if key == "MONTHLY_BUDGET_USD":
                try:
                    value = f"{max(0.0, min(1000.0, float(value.replace(',', '.')))):.2f}"
                except ValueError:
                    return jsonify(error="Budget bitte als Zahl angeben, z. B. 10."), 400
            updates[key] = value
    if updates:
        _write_env(updates)
    return get_settings()


# ---------------------------------------------------------------- Start

def _lan_ip() -> str | None:
    """Ermittelt die Adresse dieses Computers im WLAN (es wird dabei nichts gesendet)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
            return None if ip.startswith("127.") else ip
    except OSError:
        return None


def _print_banner():
    print("\n" + "=" * 60)
    print("  🎬 TikTok-KI-Generator läuft!")
    print(f"  Am Computer:   http://127.0.0.1:{PORT}")
    ip = _lan_ip() if PHONE_ACCESS else None
    if ip:
        phone = f"http://{ip}:{PORT}"
        print(f"  Am iPhone:     {phone}   (im selben WLAN)")
        print(f"  Zugangscode:   {ACCESS_CODE}")
        print("\n  📱 Scanne diesen QR-Code mit der iPhone-Kamera:\n")
        try:
            import qrcode
            qr = qrcode.QRCode(border=1)
            qr.add_data(f"{phone}/?code={ACCESS_CODE}")
            qr.print_ascii(invert=True)
        except Exception:
            print("  (QR-Code nicht verfügbar – Adresse oben in Safari eintippen)")
    elif PHONE_ACCESS:
        print("  📱 Kein WLAN gefunden – iPhone-Zugriff erst möglich, wenn der Computer im WLAN ist.")
    print("\n  Zum Beenden dieses Fenster schließen (oder Strg+C).")
    print("=" * 60 + "\n")


def main():
    _print_banner()
    if os.getenv("NO_BROWSER") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # keine technischen Meldungen im Fenster
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
