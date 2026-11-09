"""Physics-inspired synthetic acoustic data for the 4 SynthLeak classes.

IMPORTANT: this is *synthetic* data. Accuracy measured on it shows the pipeline
works, not how it performs on a real buried pipe. Real recordings (see
``real_audio.py``) should be mixed in / evaluated separately whenever available.

Class recipes
  0 NORMAL_FLOW      low-frequency turbulent flow rumble, slow amplitude drift
  1 AMBIENT_URBAN    traffic swells, HVAC hum (harmonics), footsteps, horns (+ faint flow)
  2 PINHOLE_LEAK     steady band-limited hiss (~1.5-8 kHz) with a resonance peak, over background
  3 CAVITATION_BURST irregular broadband transient bursts + low thump, over background
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from scipy.special import expit

from shared.constants import (
    CLASS_AMBIENT_URBAN,
    CLASS_CAVITATION_BURST,
    CLASS_NORMAL_FLOW,
    CLASS_PINHOLE_LEAK,
    CLIP_SAMPLES,
    SAMPLE_RATE,
)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64))) + 1e-12)


def _unit(x: np.ndarray) -> np.ndarray:
    return (x / _rms(x)).astype(np.float64)


def _shaped_noise(n: int, rng: np.random.Generator, lo: float, hi: float, tilt_db_oct: float = 0.0,
                  edge_hz: float = 50.0) -> np.ndarray:
    """White noise filtered in the frequency domain to [lo, hi] Hz with soft edges and spectral tilt."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
    gain = expit((f - lo) / edge_hz) * expit(-(f - hi) / edge_hz)
    if tilt_db_oct:
        gain = gain * 10.0 ** (tilt_db_oct * np.log2(np.maximum(f, 50.0) / 1000.0) / 20.0)
    return _unit(np.fft.irfft(spec * gain, n))


def _smooth_envelope(n: int, rng: np.random.Generator, rate_hz: float, depth: float) -> np.ndarray:
    """Slowly varying positive envelope around 1."""
    env = _shaped_noise(n, rng, 0.05, max(rate_hz, 0.2), edge_hz=0.2)
    return np.clip(1.0 + depth * env, 0.05, None)


def normal_flow(n: int, rng: np.random.Generator) -> np.ndarray:
    cutoff = rng.uniform(300.0, 1500.0)
    x = _shaped_noise(n, rng, 20.0, cutoff, tilt_db_oct=-rng.uniform(0.0, 6.0))
    x = x * _smooth_envelope(n, rng, rng.uniform(0.3, 1.5), rng.uniform(0.05, 0.3))
    x += 10 ** (rng.uniform(-45, -30) / 20) * rng.standard_normal(n)  # faint broadband floor
    return _unit(x)


def ambient_urban(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n) / SAMPLE_RATE
    parts: list[Tuple[np.ndarray, float]] = []
    kinds = rng.choice(["traffic", "hvac", "steps", "horn"], size=rng.integers(1, 4), replace=False)
    for k in kinds:
        if k == "traffic":
            x = _shaped_noise(n, rng, 40.0, rng.uniform(500.0, 1200.0), tilt_db_oct=-rng.uniform(3, 9))
            x *= _smooth_envelope(n, rng, rng.uniform(0.5, 2.5), rng.uniform(0.4, 0.9))
        elif k == "hvac":
            f0 = rng.uniform(50.0, 180.0)
            x = sum(rng.uniform(0.2, 1.0) / h * np.sin(2 * np.pi * f0 * h * t + rng.uniform(0, 6.28))
                    for h in range(1, int(rng.integers(3, 7))))
            x = _unit(np.asarray(x) + 0.3 * _shaped_noise(n, rng, 100.0, 2000.0))
        elif k == "steps":
            x = np.zeros(n)
            period = int(rng.uniform(0.45, 0.8) * SAMPLE_RATE)
            for s in range(int(rng.integers(0, period)), n, period):
                L = min(int(rng.uniform(0.05, 0.12) * SAMPLE_RATE), n - s)
                thump = _shaped_noise(L, rng, 50.0, 500.0) * np.exp(-np.arange(L) / (0.03 * SAMPLE_RATE))
                x[s:s + L] += thump * rng.uniform(0.6, 1.4)
            x = _unit(x) if _rms(x) > 1e-6 else x
        else:  # horn
            f0 = rng.uniform(350.0, 650.0)
            dur = rng.uniform(0.2, 0.8)
            start = rng.uniform(0, max(n / SAMPLE_RATE - dur, 0.01))
            env = np.clip(np.minimum((t - start) / 0.03, (start + dur - t) / 0.05), 0, 1)
            x = _unit(env * sum(np.sin(2 * np.pi * f0 * h * t) / h for h in (1, 2, 3)))
            x = x if _rms(x) > 1e-6 else np.zeros(n)
        parts.append((x, 10 ** (rng.uniform(-12, 0) / 20)))
    mix = sum(w * p for p, w in parts)
    mix = mix + 10 ** (rng.uniform(-30, -15) / 20) * normal_flow(n, rng)  # pipe flow underneath
    return _unit(mix)


def pinhole_leak_hiss(n: int, rng: np.random.Generator) -> np.ndarray:
    lo, hi = rng.uniform(1200.0, 2500.0), rng.uniform(5000.0, 9000.0)
    x = _shaped_noise(n, rng, lo, hi, tilt_db_oct=-rng.uniform(0.0, 4.0), edge_hz=rng.uniform(100, 400))
    if rng.random() < 0.7:  # jet resonance peak
        f = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
        peak, width, gain_db = rng.uniform(2500.0, 6500.0), rng.uniform(300.0, 900.0), rng.uniform(4.0, 12.0)
        shape = 1.0 + (10 ** (gain_db / 20) - 1.0) * np.exp(-0.5 * ((f - peak) / width) ** 2)
        x = np.fft.irfft(np.fft.rfft(x) * shape, n)
    x = x * _smooth_envelope(n, rng, rng.uniform(2.0, 15.0), rng.uniform(0.0, 0.12))
    return _unit(x)


def cavitation_bursts(n: int, rng: np.random.Generator) -> np.ndarray:
    x = np.zeros(n)
    for _ in range(int(rng.integers(3, 13))):
        L = int(rng.uniform(0.005, 0.04) * SAMPLE_RATE)
        s = int(rng.integers(0, n - L))
        burst = _shaped_noise(L, rng, rng.uniform(200, 900), rng.uniform(4000, 10000), edge_hz=200)
        x[s:s + L] += burst * np.exp(-np.arange(L) / (L / rng.uniform(2.0, 5.0))) * rng.lognormal(0.0, 0.6)
    if rng.random() < 0.6:  # hydraulic-hammer thump
        L = int(rng.uniform(0.1, 0.3) * SAMPLE_RATE)
        s = int(rng.integers(0, n - L))
        x[s:s + L] += 2.0 * _shaped_noise(L, rng, 30, 200) * np.exp(-np.arange(L) / (0.05 * SAMPLE_RATE))
    x += 0.05 * _shaped_noise(n, rng, 1500, 8000)  # faint continuous hiss
    return _unit(x)


def _background(n: int, rng: np.random.Generator) -> np.ndarray:
    r = rng.random()
    if r < 0.4:
        return ambient_urban(n, rng)
    if r < 0.7:
        return normal_flow(n, rng)
    return _unit(ambient_urban(n, rng) + normal_flow(n, rng))


def make_sample(
    class_id: int,
    rng: np.random.Generator,
    snr_db: Optional[float] = None,
    snr_range: Tuple[float, float] = (-3.0, 20.0),
    n: int = CLIP_SAMPLES,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return ``(clip, background_reference)``.

    ``background_reference`` is an independent background-only clip (different draw),
    used to calibrate Adaptive Noise Suppression the way a field install would.
    For leak/burst classes ``snr_db`` is signal-to-background in dB (random in
    ``snr_range`` if None); for classes 0/1 it is ignored.
    """
    if class_id == CLASS_NORMAL_FLOW:
        sig = normal_flow(n, rng)
    elif class_id == CLASS_AMBIENT_URBAN:
        sig = ambient_urban(n, rng)
    elif class_id in (CLASS_PINHOLE_LEAK, CLASS_CAVITATION_BURST):
        src = pinhole_leak_hiss(n, rng) if class_id == CLASS_PINHOLE_LEAK else cavitation_bursts(n, rng)
        snr = rng.uniform(*snr_range) if snr_db is None else float(snr_db)
        bg = _background(n, rng)
        sig = src * 10 ** (snr / 20.0) + bg
    else:
        raise ValueError(f"Unknown class_id {class_id}")
    sig = sig + 10 ** (rng.uniform(-70, -55) / 20) * rng.standard_normal(n)  # mic self-noise
    level_db = rng.uniform(-30.0, -8.0)  # overall loudness (dBFS RMS)
    sig = sig / _rms(sig) * 10 ** (level_db / 20.0)
    sig = np.clip(sig, -0.99, 0.99)
    return sig.astype(np.float32), (_background(n, rng) * 10 ** (level_db / 20.0)).astype(np.float32)
