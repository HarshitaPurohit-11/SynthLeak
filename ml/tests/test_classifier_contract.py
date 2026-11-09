"""Contract tests for LeakClassifier. Need PyTorch; skipped automatically without it.

Uses a freshly initialised (untrained) network so no weights file is required:
the point is the interface (CONTRACT.md section 4), not accuracy.
"""

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from ml.classifier import LeakClassifier  # noqa: E402
from ml.model import DEFAULT_WIDTHS, LeakCNN, build_model  # noqa: E402
from shared.constants import CLASS_LABELS, CLIP_SAMPLES, N_FFT, SAMPLE_RATE  # noqa: E402
from shared.schemas import InferenceOutput  # noqa: E402


@pytest.fixture()
def clf(tmp_path):
    path = tmp_path / "tmp_weights.pt"
    torch.save({"state_dict": build_model().state_dict(),
                "config": {"widths": list(DEFAULT_WIDTHS), "dropout": 0.3},
                "meta": {"note": "untrained test weights"}}, path)
    return LeakClassifier(weights_path=path)


def test_model_output_shape():
    out = LeakCNN()(torch.zeros(2, 1, 128, 128))
    assert out.shape == (2, 4)


def test_predict_matches_inference_schema(clf):
    t = np.arange(CLIP_SAMPLES) / SAMPLE_RATE
    audio = (0.3 * np.sin(2 * np.pi * 4200 * t)).astype(np.float32)
    result = clf.predict(audio, SAMPLE_RATE)
    validated = InferenceOutput(**result)  # raises if the contract is violated
    assert CLASS_LABELS[validated.class_id] == validated.class_label
    assert 0.0 <= validated.confidence <= 1.0
    assert abs(validated.peak_frequency_hz - 4200) < 60
    assert result["timestamp"].endswith("Z") and len(result["timestamp"]) == 24


def test_predict_accepts_arbitrary_length_and_float64(clf):
    assert InferenceOutput(**clf.predict(np.random.randn(N_FFT * 3))).class_id in range(4)
    assert InferenceOutput(**clf.predict(np.random.randn(CLIP_SAMPLES * 2).astype(np.float32))).class_id in range(4)


@pytest.mark.parametrize("bad", [np.array([]), np.zeros((2, 4096)), np.full(CLIP_SAMPLES, np.nan)])
def test_predict_rejects_invalid_audio(clf, bad):
    with pytest.raises(ValueError):
        clf.predict(bad)


def test_predict_rejects_too_short(clf):
    with pytest.raises(ValueError, match="too short"):
        clf.predict(np.zeros(N_FFT - 1, dtype=np.float32))


def test_missing_weights_raise_runtime_error(tmp_path):
    with pytest.raises(RuntimeError):
        LeakClassifier(weights_path=tmp_path / "nope.pt").predict(np.zeros(CLIP_SAMPLES, dtype=np.float32))


def test_ans_toggle_and_calibration(clf):
    rng = np.random.default_rng(0)
    bg = (0.1 * rng.standard_normal(CLIP_SAMPLES)).astype(np.float32)
    clf.use_ans = True
    clf.calibrate(bg)
    assert clf.ans.is_calibrated
    InferenceOutput(**clf.predict(bg))
    clf.reset_calibration()
    assert not clf.ans.is_calibrated
