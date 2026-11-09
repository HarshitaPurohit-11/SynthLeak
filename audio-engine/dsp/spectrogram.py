"""STFT, Mel spectrogram and spectral metrics.

All parameters come from ``shared/constants.py``. A ``CLIP_SAMPLES`` (65 536)
clip with ``center=True`` framing yields 129 STFT frames; the first 128 are kept
so the output is exactly ``SPECTROGRAM_SHAPE = (128, 128)`` (mel bins x frames).
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from shared.constants import (
    FILTER_HIGH_CUT_HZ,
    FILTER_LOW_CUT_HZ,
    HOP_LENGTH,
    N_FFT,
    N_MELS,
    SAMPLE_RATE,
    SPECTROGRAM_SHAPE,
)

_EPS = 1e-10
_MEL_CACHE: dict[tuple, np.ndarray] = {}


def _hz_to_mel(f):
    """Slaney mel scale (linear below 1 kHz, log above) - same as librosa default."""
    f = np.asarray(f, dtype=np.float64)
    f_sp, min_log_hz = 200.0 / 3.0, 1000.0
    min_log_mel = min_log_hz / f_sp
    logstep = np.log(6.4) / 27.0
    return np.where(f >= min_log_hz, min_log_mel + np.log(np.maximum(f, 1e-9) / min_log_hz) / logstep, f / f_sp)


def _mel_to_hz(m):
    m = np.asarray(m, dtype=np.float64)
    f_sp, min_log_hz = 200.0 / 3.0, 1000.0
    min_log_mel = min_log_hz / f_sp
    logstep = np.log(6.4) / 27.0
    return np.where(m >= min_log_mel, min_log_hz * np.exp(logstep * (m - min_log_mel)), f_sp * m)


def mel_filterbank(
    sample_rate: int = SAMPLE_RATE,
    n_fft: int = N_FFT,
    n_mels: int = N_MELS,
    fmin: float = FILTER_LOW_CUT_HZ,
    fmax: float = FILTER_HIGH_CUT_HZ,
) -> np.ndarray:
    """Triangular Slaney-normalised Mel filterbank, shape ``(n_mels, n_fft//2+1)``.

    The Mel range is the DSP band (100 Hz - 10 kHz) so no bins are wasted on
    frequencies the bandpass removes.
    """
    key = (sample_rate, n_fft, n_mels, fmin, fmax)
    if key in _MEL_CACHE:
        return _MEL_CACHE[key]
    fft_freqs = np.linspace(0.0, sample_rate / 2.0, n_fft // 2 + 1)
    mel_pts = np.linspace(_hz_to_mel(fmin), _hz_to_mel(fmax), n_mels + 2)
    hz_pts = _mel_to_hz(mel_pts)
    fdiff = np.diff(hz_pts)
    ramps = hz_pts[:, None] - fft_freqs[None, :]
    lower = -ramps[:-2] / fdiff[:-1, None]
    upper = ramps[2:] / fdiff[1:, None]
    weights = np.maximum(0.0, np.minimum(lower, upper))
    weights *= (2.0 / (hz_pts[2 : n_mels + 2] - hz_pts[:n_mels]))[:, None]  # Slaney area norm
    _MEL_CACHE[key] = weights.astype(np.float32)
    return _MEL_CACHE[key]


def stft_magnitude(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Hann-window STFT magnitude, shape ``(N_FFT//2+1, frames)`` (centered frames)."""
    x = np.asarray(audio, dtype=np.float64)
    if x.size < N_FFT:
        x = np.pad(x, (0, N_FFT - x.size))
    padded = np.pad(x, (N_FFT // 2, N_FFT // 2), mode="reflect")
    _, _, zxx = signal.stft(
        padded, fs=sample_rate, window="hann", nperseg=N_FFT, noverlap=N_FFT - HOP_LENGTH,
        boundary=None, padded=False,
    )
    # scipy scales by 1/sum(window); undo so magnitudes are comparable to a plain FFT.
    return (np.abs(zxx) * np.sum(signal.get_window("hann", N_FFT))).astype(np.float32)


def mel_spectrogram(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Power Mel spectrogram, shape ``(N_MELS, frames)``."""
    power = stft_magnitude(audio, sample_rate) ** 2
    return (mel_filterbank(sample_rate) @ power).astype(np.float32)


def log_mel_spectrogram(audio: np.ndarray, sample_rate: int = SAMPLE_RATE, fixed_frames: bool = True) -> np.ndarray:
    """dB-scaled Mel spectrogram normalised to roughly [0, 1] for the CNN.

    Uses a fixed dynamic range (80 dB below a fixed reference) instead of per-clip
    min/max, so absolute loudness is preserved as a cue (a loud leak differs from
    a quiet hum). Shape ``SPECTROGRAM_SHAPE`` when ``fixed_frames`` is True.
    """
    mel = mel_spectrogram(audio, sample_rate)
    if fixed_frames:
        frames = SPECTROGRAM_SHAPE[1]
        mel = mel[:, :frames] if mel.shape[1] >= frames else np.pad(mel, ((0, 0), (0, frames - mel.shape[1])), constant_values=0.0)
    db = 10.0 * np.log10(mel + _EPS)
    # Reference: full-scale sine ~ (N_FFT/4)^2 energy in one bin; 80 dB window below it.
    ref_db = 10.0 * np.log10((N_FFT / 2.0) ** 2)
    norm = (db - (ref_db - 80.0)) / 80.0
    return np.clip(norm, 0.0, 1.0).astype(np.float32)


def mel_frames_normalized(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Per-frame Mel energies in [0, 1], shape ``(frames, N_MELS)`` - for the WebSocket stream."""
    return log_mel_spectrogram(audio, sample_rate, fixed_frames=False).T


def dominant_frequency_hz(
    audio: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    low_hz: float = FILTER_LOW_CUT_HZ,
    high_hz: float = FILTER_HIGH_CUT_HZ,
) -> float:
    """Frequency (Hz) of the maximum of the time-averaged, lightly smoothed power spectrum.

    Averaging over frames (Welch-style) and smoothing over ~5 bins stops a single
    noisy bin from being reported as the leak frequency.
    """
    power = np.mean(stft_magnitude(audio, sample_rate) ** 2, axis=1)
    freqs = np.linspace(0.0, sample_rate / 2.0, power.size)
    power = np.convolve(power, np.ones(5) / 5.0, mode="same")
    band = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band) or float(np.max(power[band])) <= 0.0:
        return 0.0
    idx = int(np.argmax(np.where(band, power, 0.0)))
    return float(freqs[idx])


def rms_dbfs(audio: np.ndarray) -> float:
    """RMS level in dBFS, clipped to the contract range [-90, 0]."""
    x = np.asarray(audio, dtype=np.float64)
    if x.size == 0:
        return -90.0
    rms = float(np.sqrt(np.mean(x ** 2)))
    return float(np.clip(20.0 * np.log10(max(rms, 1e-12)), -90.0, 0.0))
