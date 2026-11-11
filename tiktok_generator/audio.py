"""Audio-Pipeline: Stimmen, Musik je Format, Mischung mit Ducking und Lautheits-Normalisierung.

Alles kostenlos:
  - Stimmen: Microsoft Edge TTS (Internet nötig). Figuren in Rätseln bekommen eigene Stimmen.
  - Musik: wird hier selbst komponiert (keine Lizenzfragen). Eigene MP3s mit geklärten Rechten
    können in assets/music/<stil>/ abgelegt werden und haben dann Vorrang.
  - Mischung: Musik wird automatisch leiser, sobald gesprochen wird (Ducking); Stimme wird auf eine
    einheitliche Lautheit gebracht; ein Limiter verhindert Übersteuerung (Clipping).
"""

import math
import random
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

RATE = 44100

# ------------------------------------------------------------------ Stimmen

VOICES = [  # (ID, Name, Geschlecht)
    ("de-DE-FlorianMultilingualNeural", "Florian – natürlich, männlich", "m"),
    ("de-DE-SeraphinaMultilingualNeural", "Seraphina – natürlich, weiblich", "f"),
    ("de-DE-ConradNeural", "Conrad – tief, männlich", "m"),
    ("de-DE-KatjaNeural", "Katja – klar, weiblich", "f"),
    ("de-DE-KillianNeural", "Killian – jung, männlich", "m"),
    ("de-DE-AmalaNeural", "Amala – warm, weiblich", "f"),
    ("de-AT-JonasNeural", "Jonas – österreichisch", "m"),
    ("de-AT-IngridNeural", "Ingrid – österreichisch", "f"),
    ("de-CH-JanNeural", "Jan – schweizerisch", "m"),
    ("de-CH-LeniNeural", "Leni – schweizerisch", "f"),
]
VOICE_STYLES = {  # Sprechweise: Tempo und Tonhöhe (dezent, nicht künstlich übertrieben)
    "normal": {"name": "Normal", "rate": "+5%", "pitch": "+0Hz"},
    "spannung": {"name": "Spannend", "rate": "+7%", "pitch": "-1Hz"},
    "mystery": {"name": "Mystery (ruhig, tiefer)", "rate": "-6%", "pitch": "-3Hz"},
    "ruhig": {"name": "Ruhig erzählend", "rate": "-3%", "pitch": "-2Hz"},
}
FEMALE_HINTS = ("in", "frau")
FEMALE_NAMES = {"lena", "mira", "sophie", "nora", "aylin", "greta", "anna", "emma", "lea", "lina", "sara", "zoe"}


def _is_female(name: str, role: str) -> bool:
    first = name.split()[0].lower()
    r = (role or name.split()[0]).lower()
    return first in FEMALE_NAMES or r.endswith(FEMALE_HINTS)


def assign_voices(characters, narrator: str) -> dict[str, str]:
    """Jede Figur bekommt eine eigene Stimme (passend zum Geschlecht, nicht die des Erzählers)."""
    male = [v for v, _, g in VOICES if g == "m" and v != narrator]
    female = [v for v, _, g in VOICES if g == "f" and v != narrator]
    out, mi, fi = {}, 0, 0
    for c in characters:
        if c.voice:
            out[c.name] = c.voice
        elif _is_female(c.name, c.role):
            out[c.name] = female[fi % len(female)]
            fi += 1
        else:
            out[c.name] = male[mi % len(male)]
            mi += 1
    return out


# ------------------------------------------------------------------ Musik (selbst komponiert)

MUSIC_STYLES = {
    "spannung": "Spannung (pulsierend)", "ueberwachung": "Überwachung (Brummen, Stille)",
    "abenteuer": "Abenteuer (Trommeln)", "detektiv": "Detektiv (Noir-Bass)",
    "level": "Unheimlich (schwebend)", "doku": "Doku (ruhig, episch)",
}


def _t(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def _note(freq, dur, decay=4.0, harmonics=(1.0, 0.4, 0.2)):
    t = _t(dur)
    tone = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(harmonics))
    env = np.minimum(1, t / 0.01) * np.exp(-t * decay)
    return tone * env


def _pad(freqs, dur, attack=1.5):
    t = _t(dur)
    tone = sum(np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    env = np.clip(t / attack, 0, 1) * np.clip((dur - t) / attack, 0, 1)
    return tone * env


def _place(buf, sig, start):
    i = int(start * RATE)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def _lowpass(x, cutoff):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / RATE)
    spec *= 1 / (1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spec, len(x))


def _reverb(x, seconds=1.6, mix=0.35, seed=1):
    """Einfacher Hall per FFT-Faltung mit abklingendem Rauschen."""
    rng = np.random.default_rng(seed)
    ir_t = _t(seconds)
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.0)
    n = 1 << int(math.ceil(math.log2(len(x) + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)]
    wet /= (np.abs(wet).max() + 1e-9)
    return x * (1 - mix) + wet * mix * (np.abs(x).max() + 1e-9)


def _kick(dur=0.4):
    t = _t(dur)
    return np.sin(2 * np.pi * (55 * t - 40 * t ** 2)) * np.exp(-t * 11)


def _hat(rng, dur=0.08):
    t = _t(dur)
    return rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.25


def generate_music(style: str, duration: float, seed: int = 7) -> np.ndarray:
    """Komponiert einen Musikteppich im gewünschten Stil (Stereo, float32, 44,1 kHz)."""
    rng = np.random.default_rng(seed)
    n = int(duration * RATE)
    buf = np.zeros(n)
    if style == "spannung":            # pulsierender Achtel-Bass in Moll + Pad + leises Hi-Hat
        bpm = 112
        beat = 60 / bpm
        roots = [55.0, 55.0, 46.25, 49.0]          # A, A, F#, G
        for i, tt in enumerate(np.arange(0, duration, beat / 2)):
            root = roots[int(tt / (beat * 8)) % len(roots)]
            _place(buf, _note(root, beat / 2, 9, (1, 0.6, 0.3, 0.15)) * 0.5, tt)
            if i % 2 == 1:
                _place(buf, _hat(rng), tt)
        for k, tt in enumerate(np.arange(0, duration, beat * 8)):
            r = roots[k % len(roots)] * 4
            _place(buf, _pad([r, r * 1.189, r * 1.498], beat * 8 + 1, 1.0) * 0.12, tt)
    elif style == "ueberwachung":      # Netzbrummen, Rauschen, seltene hohe Töne
        t = _t(duration)
        buf += (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t)) * 0.12
        buf += _lowpass(rng.standard_normal(n), 900) * 0.05
        for tt in np.arange(1.5, duration, 3.3):
            _place(buf, _note(rng.choice([1567.98, 1760.0, 2093.0]), 2.0, 2.0, (1, 0.1)) * 0.12, tt + rng.uniform(0, 0.8))
        buf += _pad([110.0, 116.54], duration, 3.0) * 0.06    # leicht dissonant
    elif style == "abenteuer":         # Trommeln + offene Quinten
        bpm = 100
        beat = 60 / bpm
        for i, tt in enumerate(np.arange(0, duration, beat)):
            _place(buf, _kick() * (0.8 if i % 4 == 0 else 0.45), tt)
            if i % 2 == 1:
                _place(buf, _note(98.0, 0.3, 14, (1, 0.5)) * 0.35, tt + beat / 2)
        for k, tt in enumerate(np.arange(0, duration, beat * 8)):
            r = [73.42, 65.41, 87.31, 82.41][k % 4]
            _place(buf, _pad([r * 2, r * 3, r * 4], beat * 8 + 1, 1.2) * 0.12, tt)
    elif style == "detektiv":          # Noir: gehender Bass + Moll-Septakkorde + Besen
        bpm = 88
        beat = 60 / bpm
        walk = [73.42, 87.31, 98.0, 110.0, 103.83, 98.0, 87.31, 82.41]
        for i, tt in enumerate(np.arange(0, duration, beat)):
            _place(buf, _note(walk[i % len(walk)], beat * 0.9, 5, (1, 0.5, 0.25)) * 0.45, tt)
            if i % 2 == 1:
                _place(buf, rng.standard_normal(int(0.15 * RATE)) * np.exp(-_t(0.15) * 18) * 0.08, tt)
        for k, tt in enumerate(np.arange(0, duration, beat * 8)):
            _place(buf, _pad([293.66, 349.23, 440.0, 523.25], beat * 8 + 1, 1.5) * 0.06, tt)
    elif style == "level":             # schwebend, verstimmt, leise Arpeggien mit Hall
        t = _t(duration)
        buf += (np.sin(2 * np.pi * 110 * t) + np.sin(2 * np.pi * 111.3 * t)) * 0.10
        notes = [440.0, 523.25, 622.25, 493.88]
        for i, tt in enumerate(np.arange(0.5, duration, 1.6)):
            wob = 1 + 0.004 * math.sin(i)
            _place(buf, _note(notes[i % len(notes)] * wob, 1.5, 2.5, (1, 0.2)) * 0.10, tt)
        buf = _reverb(buf, 2.4, 0.5, seed)
    else:                               # "doku": Moll-Akkorde + ruhiger Herzschlag
        chords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (130.81, 164.81, 196.0), (82.41, 103.83, 123.47)]
        for k, tt in enumerate(np.arange(0, duration, 4.0)):
            _place(buf, _pad(chords[k % 4], 5.0, 1.2) * 0.18, tt)
        for tt in np.arange(2.0, duration, 60 / 80):
            _place(buf, _kick(0.35) * 0.35, tt)
    if style not in ("level",):
        buf = _reverb(buf, 1.2, 0.18, seed)
    fade = np.clip(_t(duration) / 1.2, 0, 1) * np.clip((duration - _t(duration)) / 1.8, 0, 1)
    buf = buf * fade[: len(buf)]
    buf /= (np.abs(buf).max() + 1e-9)
    # leichte Stereobreite
    left = buf
    right = np.roll(buf, int(0.012 * RATE))
    return np.column_stack([left, right]).astype(np.float32)


def load_user_music(cfg, style: str, duration: float) -> np.ndarray | None:
    """Eigene Musik aus assets/music/<stil>/ (falls vorhanden)."""
    folder = cfg.music_dir / style
    tracks = [p for p in folder.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}] if folder.exists() else []
    if not tracks:
        return None
    from moviepy import AudioFileClip

    with AudioFileClip(str(random.choice(tracks))) as clip:
        arr = clip.to_soundarray(fps=RATE)
    if arr.ndim == 1:
        arr = np.column_stack([arr, arr])
    reps = int(math.ceil(duration * RATE / len(arr)))
    arr = np.tile(arr, (reps, 1))[: int(duration * RATE)]
    fade = np.clip(_t(duration) / 1.0, 0, 1) * np.clip((duration - _t(duration)) / 2.0, 0, 1)
    return (arr * fade[: len(arr), None] / (np.abs(arr).max() + 1e-9)).astype(np.float32)


def write_wav(path: Path, stereo: np.ndarray):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


# ------------------------------------------------------------------ Mischung

@dataclass
class MixReport:
    voice_db: float = -99.0          # Lautheit der Stimme während des Sprechens (RMS, dBFS)
    music_under_voice_db: float = -99.0
    music_gap_db: float = 0.0        # Abstand Stimme – Musik während des Sprechens (dB, größer = besser)
    peak_db: float = -99.0
    clipped_before_limiter: int = 0
    speech_seconds: float = 0.0
    notes: list = field(default_factory=list)


def _db(x):
    return 20 * math.log10(max(1e-9, x))


def _rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def mix(total: float, voices: list[tuple[np.ndarray, float]], speech_spans: list[tuple[float, float]],
        effects: list[tuple[np.ndarray, float, float]], music: np.ndarray, music_level_db: float = -26.0,
        duck_db: float = -11.0, voice_target_db: float = -16.0) -> tuple[np.ndarray, MixReport]:
    """Mischt Stimme, Effekte und Musik.

    voices:       (Stereo-Array, Startzeit)
    speech_spans: Zeitbereiche, in denen gesprochen wird (aus den Wortzeitstempeln)
    effects:      (Stereo-Array, Startzeit, Lautstärke)
    """
    n = int(total * RATE)
    report = MixReport()
    voice = np.zeros((n, 2), dtype=np.float32)
    for arr, start in voices:
        i = int(start * RATE)
        if i < n:
            m = min(len(arr), n - i)
            voice[i:i + m] += arr[:m]

    # Sprach-Maske: aus den Wortzeiten (funktioniert auch, wenn die Stimme offline stumm ist)
    mask = np.zeros(n, dtype=np.float32)
    for a, b in speech_spans:
        mask[int(max(0, a - 0.05) * RATE): int(min(total, b + 0.12) * RATE)] = 1.0
    report.speech_seconds = float(mask.sum() / RATE)
    # weich ein-/ausblenden: Angriff ~60 ms, Freigabe ~350 ms
    win = int(0.35 * RATE)
    csum = np.concatenate([[0.0], np.cumsum(mask, dtype=np.float64)])   # gleitender Mittelwert (schnell)
    idx = np.arange(n)
    lo, hi = np.clip(idx - win // 2, 0, n), np.clip(idx + win // 2, 0, n)
    smooth = ((csum[hi] - csum[lo]) / np.maximum(1, hi - lo)).astype(np.float32)
    smooth = np.clip(smooth * 1.6, 0, 1)

    # Stimme auf Ziel-Lautheit bringen (nur hörbare Sprache messen)
    speaking = mask > 0.5
    v_rms = _rms(voice[speaking].mean(axis=1)) if speaking.any() else 0.0
    if v_rms > 1e-4:
        voice *= 10 ** (voice_target_db / 20) / v_rms
        report.voice_db = voice_target_db
    else:
        report.notes.append("Stimme ist stumm (Offline-Testmodus) – Lautheit nicht messbar.")

    # Musik: Grundlautstärke + Ducking während der Sprache
    mus = np.zeros((n, 2), dtype=np.float32)
    m = min(n, len(music))
    mus[:m] = music[:m]
    m_rms = _rms(mus[~speaking].mean(axis=1)) if (~speaking).any() else _rms(mus.mean(axis=1))
    if m_rms > 1e-6:
        mus *= 10 ** (music_level_db / 20) / m_rms
    gain = 1 - (1 - 10 ** (duck_db / 20)) * smooth
    mus *= gain[:, None]
    if speaking.any():
        report.music_under_voice_db = _db(_rms(mus[speaking].mean(axis=1)))
        if report.voice_db > -90:
            report.music_gap_db = report.voice_db - report.music_under_voice_db

    fx = np.zeros((n, 2), dtype=np.float32)
    for arr, start, vol in effects:
        i = int(max(0.0, start) * RATE)
        if i < n:
            k = min(len(arr), n - i)
            fx[i:i + k] += arr[:k] * vol * 10 ** (-9 / 20)   # Effekte ca. 9 dB unter der Stimme

    out = voice + mus + fx
    report.clipped_before_limiter = int((np.abs(out) > 1.0).sum())
    # Limiter: weich bei -1 dBFS begrenzen (kein hartes Clipping)
    ceiling = 10 ** (-1 / 20)
    over = np.abs(out) > ceiling * 0.8
    if over.any():
        out[over] = np.sign(out[over]) * (ceiling * 0.8 + (ceiling * 0.2) * np.tanh(
            (np.abs(out[over]) - ceiling * 0.8) / (ceiling * 0.2)))
    report.peak_db = _db(float(np.abs(out).max()) or 1e-9)
    return out.astype(np.float32), report
