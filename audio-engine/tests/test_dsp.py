"""Unit tests for audio-engine/dsp (run: pytest audio-engine/tests -v)."""

import numpy as np
import pytest

from dsp.filters import AdaptiveNoiseSuppressor, adaptive_spectral_subtraction, bandpass_filter
from dsp.spectrogram import (
    dominant_frequency_hz,
    log_mel_spectrogram,
    mel_filterbank,
    mel_frames_normalized,
    mel_spectrogram,
    rms_dbfs,
    stft_magnitude,
)
from shared.constants import CLIP_SAMPLES, N_FFT, N_MELS, SAMPLE_RATE, SPECTROGRAM_SHAPE


def tone(freq, amp=0.5, n=CLIP_SAMPLES):
    t = np.arange(n) / SAMPLE_RATE
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def band_power(x, lo, hi):
    spec = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(x.size, 1 / SAMPLE_RATE)
    return spec[(f >= lo) & (f <= hi)].sum()


def test_bandpass_passes_in_band_and_rejects_out_of_band():
    in_band = bandpass_filter(tone(3000))
    low = bandpass_filter(tone(30))
    assert np.std(in_band) > 0.9 * np.std(tone(3000))
    assert np.std(low) < 0.05 * np.std(tone(30))


def test_urban_preset_is_narrower():
    x = tone(300)
    assert np.std(bandpass_filter(x, preset="default")) > 5 * np.std(bandpass_filter(x, preset="urban"))


def test_bandpass_bad_inputs():
    with pytest.raises(ValueError):
        bandpass_filter(tone(1000), preset="nope")
    with pytest.raises(ValueError):
        bandpass_filter(tone(1000), low_hz=5000, high_hz=1000)


def test_bandpass_preserves_length_and_dtype():
    y = bandpass_filter(tone(1000))
    assert y.shape == (CLIP_SAMPLES,) and y.dtype == np.float32


def test_mel_filterbank_shape_and_no_empty_filters():
    fb = mel_filterbank()
    assert fb.shape == (N_MELS, N_FFT // 2 + 1)
    assert np.all(fb.sum(axis=1) > 0)


def test_mel_filterbank_matches_librosa():
    librosa = pytest.importorskip("librosa")
    ref = librosa.filters.mel(sr=SAMPLE_RATE, n_fft=N_FFT, n_mels=N_MELS, fmin=100.0, fmax=10000.0)
    np.testing.assert_allclose(mel_filterbank(), ref, rtol=1e-3, atol=1e-6)


def test_log_mel_shape_and_range():
    s = log_mel_spectrogram(tone(4000))
    assert s.shape == SPECTROGRAM_SHAPE
    assert 0.0 <= s.min() and s.max() <= 1.0
    assert np.isfinite(s).all()


def test_log_mel_short_buffer_padded():
    assert log_mel_spectrogram(tone(1000, n=2048)).shape == SPECTROGRAM_SHAPE


def test_mel_spectrogram_frame_count():
    assert mel_spectrogram(tone(1000)).shape == (N_MELS, 129)
    assert mel_frames_normalized(tone(1000)).shape[1] == N_MELS


def test_louder_signal_has_higher_mel_energy():
    assert log_mel_spectrogram(tone(2000, 0.5)).mean() > log_mel_spectrogram(tone(2000, 0.05)).mean()


@pytest.mark.parametrize("freq", [500.0, 2500.0, 4200.0, 8000.0])
def test_dominant_frequency_of_tone(freq):
    assert abs(dominant_frequency_hz(tone(freq)) - freq) < 60.0


def test_dominant_frequency_silence_is_zero():
    assert dominant_frequency_hz(np.zeros(CLIP_SAMPLES, dtype=np.float32)) == 0.0


def test_rms_dbfs():
    assert abs(rms_dbfs(tone(1000, 1.0)) - (-3.01)) < 0.1
    assert rms_dbfs(np.zeros(100)) == -90.0
    assert -90.0 <= rms_dbfs(np.ones(100) * 5) <= 0.0


def test_ans_noop_without_profile():
    x = tone(3000) + 0.1 * np.random.default_rng(0).standard_normal(CLIP_SAMPLES).astype(np.float32)
    np.testing.assert_allclose(adaptive_spectral_subtraction(x, None), x, atol=1e-6)


def test_ans_reduces_background_and_keeps_leak():
    rng = np.random.default_rng(1)
    hum = tone(200, 0.4) + 0.05 * rng.standard_normal(CLIP_SAMPLES).astype(np.float32)  # background
    leak = tone(4000, 0.2)
    ans = AdaptiveNoiseSuppressor()
    assert not ans.is_calibrated
    ans.update(hum)
    assert ans.is_calibrated
    out = ans.process(hum + leak)
    # Background (200 Hz) region drops a lot; leak (4 kHz) region survives.
    assert band_power(out, 150, 250) < 0.2 * band_power(hum + leak, 150, 250)
    assert band_power(out, 3900, 4100) > 0.7 * band_power(leak, 3900, 4100)
    assert out.shape == (CLIP_SAMPLES,)


def test_ans_reset_and_bad_profile():
    ans = AdaptiveNoiseSuppressor()
    ans.update(tone(200))
    ans.reset()
    assert not ans.is_calibrated
    with pytest.raises(ValueError):
        adaptive_spectral_subtraction(tone(200), np.ones(10))
