"""Filtering and Adaptive Noise Suppression (ANS).

* ``bandpass_filter``: 4th-order Butterworth bandpass (zero-phase, SOS form).
  Default band 100 Hz - 10 kHz; ``preset="urban"`` selects 500 Hz - 9 kHz
  (see CONTRACT.md section 2).
* ``adaptive_spectral_subtraction`` / ``AdaptiveNoiseSuppressor``: spectral
  subtraction against a *learned* noise-floor profile.

Terminology: this is **Adaptive Noise Suppression**, not "Active Noise
Cancellation".

Design note (important for Q&A): a pinhole leak is itself a *stationary* hiss, so
blind minimum-statistics noise estimation would erase the leak together with the
noise. ANS therefore subtracts a profile learned from background-only audio
(calibration at install time, or frames the classifier labelled NORMAL_FLOW /
AMBIENT_URBAN). With no profile it is a no-op.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from scipy import signal

from shared.constants import (
    FILTER_HIGH_CUT_HZ,
    FILTER_LOW_CUT_HZ,
    FILTER_URBAN_HIGH_CUT_HZ,
    FILTER_URBAN_LOW_CUT_HZ,
    HOP_LENGTH,
    N_FFT,
    SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

FILTER_ORDER: int = 4
PRESETS: dict[str, tuple[float, float]] = {
    "default": (FILTER_LOW_CUT_HZ, FILTER_HIGH_CUT_HZ),
    "urban": (FILTER_URBAN_LOW_CUT_HZ, FILTER_URBAN_HIGH_CUT_HZ),
}


def bandpass_filter(
    audio: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    low_hz: Optional[float] = None,
    high_hz: Optional[float] = None,
    preset: str = "default",
    order: int = FILTER_ORDER,
) -> np.ndarray:
    """Zero-phase Butterworth bandpass. Explicit ``low_hz``/``high_hz`` override ``preset``."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown filter preset '{preset}'. Choose from {list(PRESETS)}")
    p_low, p_high = PRESETS[preset]
    low = p_low if low_hz is None else float(low_hz)
    high = p_high if high_hz is None else float(high_hz)
    nyquist = sample_rate / 2.0
    high = min(high, nyquist * 0.99)  # keep strictly below Nyquist
    if not 0.0 < low < high:
        raise ValueError(f"Invalid band: low={low} Hz, high={high} Hz")
    sos = signal.butter(order, [low, high], btype="bandpass", fs=sample_rate, output="sos")
    x = np.asarray(audio, dtype=np.float64)
    # sosfiltfilt needs a minimum length; fall back to causal filtering for tiny buffers.
    if x.size > 3 * (2 * sos.shape[0] + 1) + 1:
        y = signal.sosfiltfilt(sos, x)
    else:
        y = signal.sosfilt(sos, x)
    return y.astype(np.float32)


def _noise_profile_from_audio(audio: np.ndarray) -> np.ndarray:
    """Mean STFT magnitude per FFT bin (shape ``(N_FFT//2+1,)``) of a background-only clip."""
    _, _, zxx = signal.stft(
        np.asarray(audio, dtype=np.float64), fs=SAMPLE_RATE, window="hann",
        nperseg=N_FFT, noverlap=N_FFT - HOP_LENGTH, boundary="zeros", padded=True,
    )
    return np.mean(np.abs(zxx), axis=1)


def adaptive_spectral_subtraction(
    audio: np.ndarray,
    noise_profile: Optional[np.ndarray],
    over_subtraction: float = 1.5,
    spectral_floor: float = 0.05,
) -> np.ndarray:
    """Subtract ``over_subtraction * noise_profile`` from the STFT magnitude, keep phase.

    ``spectral_floor`` limits how far a bin may be attenuated (reduces musical noise).
    Returns audio of the same length. ``noise_profile=None`` returns the input unchanged.
    """
    x = np.asarray(audio, dtype=np.float64)
    if noise_profile is None:
        return x.astype(np.float32)
    if noise_profile.shape[0] != N_FFT // 2 + 1:
        raise ValueError("noise_profile must have N_FFT//2+1 bins")
    _, _, zxx = signal.stft(
        x, fs=SAMPLE_RATE, window="hann", nperseg=N_FFT, noverlap=N_FFT - HOP_LENGTH,
        boundary="zeros", padded=True,
    )
    mag, phase = np.abs(zxx), np.angle(zxx)
    cleaned = mag - over_subtraction * noise_profile[:, None]
    cleaned = np.maximum(cleaned, spectral_floor * mag)
    _, y = signal.istft(
        cleaned * np.exp(1j * phase), fs=SAMPLE_RATE, window="hann", nperseg=N_FFT,
        noverlap=N_FFT - HOP_LENGTH, boundary=True,
    )
    y = y[: x.size]
    if y.size < x.size:
        y = np.pad(y, (0, x.size - y.size))
    return y.astype(np.float32)


class AdaptiveNoiseSuppressor:
    """Stateful ANS holding a running noise-floor profile.

    Usage::

        ans = AdaptiveNoiseSuppressor()
        ans.update(background_clip)      # calibration, or clips labelled NORMAL/AMBIENT
        cleaned = ans.process(new_clip)  # no-op until a profile exists
    """

    def __init__(self, smoothing: float = 0.8, over_subtraction: float = 1.5,
                 spectral_floor: float = 0.05) -> None:
        if not 0.0 <= smoothing < 1.0:
            raise ValueError("smoothing must be in [0, 1)")
        self.smoothing = smoothing
        self.over_subtraction = over_subtraction
        self.spectral_floor = spectral_floor
        self.profile: Optional[np.ndarray] = None

    @property
    def is_calibrated(self) -> bool:
        return self.profile is not None

    def update(self, background_audio: np.ndarray) -> None:
        """Exponential moving average of the background spectrum."""
        new = _noise_profile_from_audio(background_audio)
        if self.profile is None:
            self.profile = new
        else:
            self.profile = self.smoothing * self.profile + (1.0 - self.smoothing) * new

    def reset(self) -> None:
        self.profile = None

    def process(self, audio: np.ndarray) -> np.ndarray:
        return adaptive_spectral_subtraction(
            audio, self.profile, self.over_subtraction, self.spectral_floor
        )
