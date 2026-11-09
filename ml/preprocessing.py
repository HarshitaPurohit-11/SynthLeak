"""Input validation + DSP chain used by training, validation and inference.

Chain (see audio-engine/README.md): input validation -> Butterworth bandpass ->
optional Adaptive Noise Suppression -> Hann STFT -> 128-bin Mel -> dB scaling.
"""

from __future__ import annotations

import sys
from math import gcd
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.signal import resample_poly

_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT, _ROOT / "audio-engine"):  # "audio-engine" has a hyphen -> add to sys.path
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dsp.filters import AdaptiveNoiseSuppressor, bandpass_filter  # noqa: E402
from dsp.spectrogram import dominant_frequency_hz, log_mel_spectrogram, rms_dbfs  # noqa: E402
from shared.constants import CLIP_SAMPLES, N_FFT, SAMPLE_RATE  # noqa: E402


def validate_and_fit(audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Return a float32 mono clip of exactly ``CLIP_SAMPLES`` samples at ``SAMPLE_RATE``.

    Raises ``ValueError`` with the exact messages required by CONTRACT.md section 4.4.
    Longer buffers keep the most recent ``CLIP_SAMPLES``; shorter ones (>= N_FFT) are
    zero-padded at the end.
    """
    x = np.asarray(audio_data)
    if x.size == 0:
        raise ValueError("Invalid audio data: empty buffer")
    if x.ndim != 1:
        raise ValueError("Invalid audio data: expected a 1D array")
    x = x.astype(np.float32, copy=False)
    if not np.all(np.isfinite(x)):
        raise ValueError("Invalid audio data: NaN or Inf detected")
    if sample_rate != SAMPLE_RATE:
        g = gcd(int(sample_rate), SAMPLE_RATE)
        x = resample_poly(x, SAMPLE_RATE // g, int(sample_rate) // g).astype(np.float32)
    if x.size < N_FFT:
        raise ValueError("Audio buffer too short for FFT window")
    if x.size >= CLIP_SAMPLES:
        return np.ascontiguousarray(x[-CLIP_SAMPLES:])
    return np.pad(x, (0, CLIP_SAMPLES - x.size))


def dsp_chain(clip: np.ndarray, ans: Optional[AdaptiveNoiseSuppressor] = None, preset: str = "default") -> np.ndarray:
    """Bandpass (+ ANS if calibrated). Returns the cleaned time-domain clip."""
    y = bandpass_filter(clip, SAMPLE_RATE, preset=preset)
    if ans is not None and ans.is_calibrated:
        y = ans.process(y)
    return y


def calibrate_suppressor(ans: AdaptiveNoiseSuppressor, background_clip: np.ndarray, preset: str = "default") -> None:
    """Feed a background-only clip (same bandpass as the signal path) to the ANS."""
    ans.update(bandpass_filter(background_clip, SAMPLE_RATE, preset=preset))


def extract_features(clip: np.ndarray, ans: Optional[AdaptiveNoiseSuppressor] = None, preset: str = "default") -> np.ndarray:
    """``(128, 128)`` float32 log-Mel image in [0, 1] for the CNN."""
    return log_mel_spectrogram(dsp_chain(clip, ans, preset), SAMPLE_RATE)


__all__ = [
    "AdaptiveNoiseSuppressor",
    "calibrate_suppressor",
    "dominant_frequency_hz",
    "dsp_chain",
    "extract_features",
    "rms_dbfs",
    "validate_and_fit",
]
