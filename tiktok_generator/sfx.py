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


EFFECTS = {"whoosh": whoosh, "impact": impact, "boom": boom, "riser": riser, "tick": tick}


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
