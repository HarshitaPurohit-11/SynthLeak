"""Torch-free tests: input validation, synthetic data, dataset building, real-audio loader."""

import numpy as np
import pytest
from scipy.io import wavfile

from ml.preprocessing import extract_features, validate_and_fit
from ml.training.dataset import build_synthetic_dataset
from ml.training.real_audio import infer_class, load_real_clips
from ml.training.synthetic import make_sample
from shared.constants import CLASS_LABELS, CLIP_SAMPLES, N_FFT, SAMPLE_RATE, SPECTROGRAM_SHAPE


def test_validate_rejects_bad_input():
    with pytest.raises(ValueError):
        validate_and_fit(np.array([], dtype=np.float32))
    with pytest.raises(ValueError):
        validate_and_fit(np.zeros((2, 2048), dtype=np.float32))
    bad = np.zeros(CLIP_SAMPLES, dtype=np.float32)
    bad[10] = np.nan
    with pytest.raises(ValueError, match="NaN or Inf"):
        validate_and_fit(bad)
    bad[10] = np.inf
    with pytest.raises(ValueError, match="NaN or Inf"):
        validate_and_fit(bad)
    with pytest.raises(ValueError, match="too short"):
        validate_and_fit(np.zeros(N_FFT - 1, dtype=np.float32))


def test_validate_fits_length():
    assert validate_and_fit(np.zeros(N_FFT, dtype=np.float32)).shape == (CLIP_SAMPLES,)
    long = np.arange(CLIP_SAMPLES + 1000, dtype=np.float32)
    out = validate_and_fit(long)
    assert out.shape == (CLIP_SAMPLES,) and out[-1] == long[-1]  # keeps the most recent samples


def test_validate_resamples():
    x = np.zeros(48000 * 2, dtype=np.float32)
    assert validate_and_fit(x, sample_rate=48000).shape == (CLIP_SAMPLES,)


@pytest.mark.parametrize("cid", sorted(CLASS_LABELS))
def test_synthetic_samples_valid(cid):
    rng = np.random.default_rng(cid)
    clip, bg = make_sample(cid, rng)
    assert clip.shape == (CLIP_SAMPLES,) and bg.shape == (CLIP_SAMPLES,)
    assert clip.dtype == np.float32 and np.isfinite(clip).all() and np.abs(clip).max() <= 1.0
    assert extract_features(clip).shape == SPECTROGRAM_SHAPE


def test_synthetic_is_reproducible():
    a, _ = make_sample(2, np.random.default_rng(7))
    b, _ = make_sample(2, np.random.default_rng(7))
    np.testing.assert_array_equal(a, b)


def test_leak_has_more_high_frequency_energy_than_normal_flow():
    rng = np.random.default_rng(0)
    leak = np.mean([extract_features(make_sample(2, rng, snr_db=15)[0])[64:].mean() for _ in range(8)])
    normal = np.mean([extract_features(make_sample(0, rng)[0])[64:].mean() for _ in range(8)])
    assert leak > normal


def test_dataset_balanced_and_shaped():
    X, y = build_synthetic_dataset(6, seed=3, verbose=False)
    assert X.shape == (24, 128, 128) and X.dtype == np.float32
    assert sorted(np.bincount(y).tolist()) == [6, 6, 6, 6]
    assert 0.0 <= X.min() and X.max() <= 1.0


def test_real_audio_loader(tmp_path):
    (tmp_path / "leak").mkdir()
    rng = np.random.default_rng(0)
    data = (rng.standard_normal(SAMPLE_RATE * 4) * 3000).astype(np.int16)
    wavfile.write(tmp_path / "leak" / "bottle_hiss_01.wav", SAMPLE_RATE, data)
    wavfile.write(tmp_path / "mystery_file.wav", SAMPLE_RATE, data)  # no keyword -> skipped
    clips = load_real_clips(tmp_path)
    assert len(clips) == 2  # 4 s of audio -> two full 1.486 s windows
    assert all(c[1] == 2 and c[0].shape == (CLIP_SAMPLES,) for c in clips)
    assert infer_class(tmp_path / "traffic_noise.wav", tmp_path) == 1
    assert load_real_clips(tmp_path / "missing") == []
