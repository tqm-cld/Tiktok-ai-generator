"""Soundeffekte und Hintergrundmusik – komplett selbst erzeugt (keine Lizenzprobleme, kostenlos).

Effekte:  whoosh (Wischen), impact (Schlag), boom (tiefer Kino-Bass), riser (Spannungsaufbau), tick (Uhr/Zahl)
Musik:    ruhiger, düsterer "Doku"-Klangteppich mit Puls, falls kein eigenes MP3 in assets/music liegt.
"""

import numpy as np
from moviepy import AudioArrayClip

RATE = 44100


def _t(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * RATE)) / RATE


def _band_noise(n: int, low: float, high: float, rng: np.random.Generator) -> np.ndarray:
    """Rauschen, das nur Frequenzen zwischen `low` und `high` Hz enthält (per FFT gefiltert)."""
    spec = np.fft.rfft(rng.standard_normal(n))
    freqs = np.fft.rfftfreq(n, 1 / RATE)
    spec[(freqs < low) | (freqs > high)] = 0
    out = np.fft.irfft(spec, n)
    return out / (np.abs(out).max() + 1e-9)


def _stereo(mono: np.ndarray, volume: float = 1.0) -> np.ndarray:
    mono = mono / (np.abs(mono).max() + 1e-9) * volume
    return np.column_stack([mono, mono]).astype(np.float32)


def whoosh(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = _t(0.5)
    env = np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2
    low = _band_noise(len(t), 150, 900, rng)
    high = _band_noise(len(t), 900, 5000, rng)
    sweep = np.clip(t / 0.5, 0, 1)  # dunkel → hell
    return _stereo((low * (1 - sweep) + high * sweep) * env, 0.55)


def impact(seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = _t(0.9)
    body = np.sin(2 * np.pi * (70 * t - 25 * t ** 2)) * np.exp(-t * 6)
    crack = _band_noise(len(t), 200, 4000, rng) * np.exp(-t * 40)
    return _stereo(body + 0.5 * crack, 0.9)


def boom(seed: int = 2) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = _t(1.8)
    freq = 38 + 30 * np.exp(-t * 3)                       # tiefer, abfallender Bass
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    body = np.sin(phase) * np.exp(-t * 2.2)
    rumble = _band_noise(len(t), 30, 250, rng) * np.exp(-t * 3)
    hit = _band_noise(len(t), 500, 6000, rng) * np.exp(-t * 30)
    return _stereo(body + 0.4 * rumble + 0.3 * hit, 1.0)


def riser(seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dur = 1.4
    t = _t(dur)
    freq = 180 * (6 ** (t / dur))                         # steigt exponentiell
    tone = np.sin(2 * np.pi * np.cumsum(freq) / RATE)
    noise = _band_noise(len(t), 1000, 8000, rng)
    env = (t / dur) ** 2
    return _stereo((0.6 * tone + 0.4 * noise) * env, 0.45)


def tick(seed: int = 4) -> np.ndarray:
    t = _t(0.5)
    out = np.zeros_like(t)
    for start in (0.0, 0.25):                              # tick-tack
        mask = (t >= start) & (t < start + 0.03)
        tt = t[mask] - start
        out[mask] += np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 150)
    return _stereo(out, 0.5)


def clue(seed: int = 5) -> np.ndarray:
    """Heller, kurzer Doppelton – „Hinweis entdeckt“."""
    out = np.zeros(int(0.9 * RATE))
    for start, f in ((0.0, 880.0), (0.12, 1318.5)):
        t = _t(0.9 - start)
        tone = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 6)
        i = int(start * RATE)
        out[i:i + len(tone)] += tone[:len(out) - i]
    return _stereo(out, 0.45)


def countdown(seed: int = 6) -> np.ndarray:
    """Ein tiefer Uhr-Schlag pro Sekunde (3 Schläge) – passend zur 3-2-1-Anzeige."""
    out = np.zeros(int(3.0 * RATE))
    for k in range(3):
        t = _t(0.35)
        f = 520 if k < 2 else 780
        tone = np.sin(2 * np.pi * f * t) * np.exp(-t * 26) + 0.6 * np.sin(2 * np.pi * 90 * t) * np.exp(-t * 14)
        i = int(k * RATE)
        out[i:i + len(tone)] += tone
    return _stereo(out, 0.55)


def choice(seed: int = 7) -> np.ndarray:
    """Weicher „Pop“ für Entscheidungs-Karten."""
    t = _t(0.4)
    f = 300 + 500 * np.exp(-t * 20)
    tone = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 9)
    return _stereo(tone, 0.4)


def reveal(seed: int = 8) -> np.ndarray:
    """Auflösung: tiefer Schlag + heller Akkord, der ausklingt."""
    rng = np.random.default_rng(seed)
    t = _t(2.2)
    hit = np.sin(2 * np.pi * (60 * t - 10 * t ** 2)) * np.exp(-t * 3.5)
    chord = sum(np.sin(2 * np.pi * f * t) for f in (440.0, 554.4, 659.3, 880.0)) * np.exp(-t * 1.6) * 0.25
    shimmer = _band_noise(len(t), 3000, 9000, rng) * np.exp(-t * 4) * 0.15
    return _stereo(hit + chord + shimmer, 0.8)


def glitch(seed: int = 9) -> np.ndarray:
    """Kamera-Störung: kurzes, zerhacktes Rauschen."""
    rng = np.random.default_rng(seed)
    t = _t(0.6)
    noise = _band_noise(len(t), 400, 6000, rng)
    gate = (np.sin(2 * np.pi * 23 * t) > 0.2).astype(float) * np.exp(-t * 3)
    hum = np.sin(2 * np.pi * 120 * t) * 0.3
    return _stereo((noise + hum) * gate, 0.35)


EFFECTS = {"whoosh": whoosh, "impact": impact, "boom": boom, "riser": riser, "tick": tick,
           "clue": clue, "countdown": countdown, "choice": choice, "reveal": reveal, "glitch": glitch}


def effect_clip(name: str, start: float, volume: float = 1.0):
    """Gibt einen Audioclip für den Effekt zurück. Ein riser endet genau bei `start`."""
    audio = EFFECTS[name]() * volume
    clip = AudioArrayClip(audio, fps=RATE)
    if name == "riser":
        start -= clip.duration
    return clip.with_start(max(0.0, start))


def ambient_music(duration: float, seed: int = 7) -> AudioArrayClip:
    """Erzeugt einen spannungsvollen Doku-Klangteppich (Moll-Akkorde + leiser Herzschlag-Puls)."""
    rng = np.random.default_rng(seed)
    t = _t(duration)
    # Akkordfolge a-Moll – F – C – E (je 4 Sekunden), Frequenzen in Hz
    chords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (130.81, 164.81, 196.0), (82.41, 103.83, 123.47)]
    pad = np.zeros_like(t)
    seg = 4.0
    for i, chord in enumerate(chords * int(duration // (seg * 4) + 1)):
        start = i * seg
        if start >= duration:
            break
        mask = (t >= start) & (t < start + seg + 1.0)       # 1 s Überblendung
        tt = t[mask] - start
        env = np.clip(tt / 1.2, 0, 1) * np.clip((seg + 1.0 - tt) / 1.2, 0, 1)
        voice = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + 0.5) for f in chord)
        pad[mask] += voice * env
    pad *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * t)          # langsames "Atmen"

    # Puls: tiefer, weicher Schlag bei 80 BPM
    pulse = np.zeros_like(t)
    beat = 60 / 80
    kick_t = _t(0.35)
    kick = np.sin(2 * np.pi * (55 * kick_t - 30 * kick_t ** 2)) * np.exp(-kick_t * 12)
    for k in np.arange(2.0, duration, beat):                # Puls setzt nach 2 s ein
        i = int(k * RATE)
        n = min(len(kick), len(pulse) - i)
        pulse[i:i + n] += kick[:n]

    air = _band_noise(len(t), 2000, 7000, rng) * 0.03
    mix = pad / (np.abs(pad).max() + 1e-9) * 0.7 + pulse * 0.5 + air
    fade = np.clip(t / 1.5, 0, 1) * np.clip((duration - t) / 2.0, 0, 1)
    return AudioArrayClip(_stereo(mix * fade, 0.9), fps=RATE)
