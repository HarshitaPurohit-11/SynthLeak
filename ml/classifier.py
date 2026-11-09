"""Production inference callable (CONTRACT.md section 4).

    from ml.classifier import LeakClassifier
    clf = LeakClassifier()                 # loads ml/weights/leak_cnn.pt
    result = clf.predict(audio_buffer)     # dict matching shared.schemas.InferenceOutput

Thread-safe: the backend may call ``predict`` from ``asyncio.to_thread`` workers.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from ml.preprocessing import (
    AdaptiveNoiseSuppressor,
    calibrate_suppressor,
    dominant_frequency_hz,
    dsp_chain,
    validate_and_fit,
)
from dsp.spectrogram import log_mel_spectrogram
from shared.constants import CLASS_LABELS, SAMPLE_RATE

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parent / "weights" / "leak_cnn.pt"


def _utc_timestamp() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


class LeakClassifier:
    """DSP chain + CNN. Implements ``LeakClassifierInterface`` from CONTRACT.md.

    Parameters
    ----------
    weights_path: checkpoint written by ``python -m ml.training.train``.
    use_ans: apply Adaptive Noise Suppression (only effective after ``calibrate``).
    preset: ``"default"`` (100 Hz-10 kHz) or ``"urban"`` (500 Hz-9 kHz) bandpass.
    """

    def __init__(self, weights_path: Optional[str | Path] = None, device: str = "cpu",
                 use_ans: bool = False, preset: str = "default") -> None:
        self.weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self.device = device
        self.use_ans = use_ans
        self.preset = preset
        self.ans = AdaptiveNoiseSuppressor()
        self.metadata: Dict[str, Any] = {}
        self._model = None
        self._torch = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ setup
    @property
    def is_ready(self) -> bool:
        return self.weights_path.is_file()

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.weights_path.is_file():
            raise RuntimeError(
                f"Model weights not found at {self.weights_path}. "
                "Train them with: python -m ml.training.train"
            )
        try:
            import torch
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("PyTorch is not installed. Run: pip install -r ml/requirements-ml.txt") from exc
        from ml.model import build_model

        try:
            ckpt = torch.load(self.weights_path, map_location=self.device, weights_only=True)
            cfg = ckpt.get("config", {})
            model = build_model(tuple(cfg.get("widths", (16, 32, 64, 96))), cfg.get("dropout", 0.3))
            model.load_state_dict(ckpt["state_dict"])
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to load model weights from {self.weights_path}: {exc}") from exc
        model.to(self.device).eval()
        self._torch, self._model = torch, model
        self.metadata = dict(ckpt.get("meta", {}))
        logger.info("Loaded LeakCNN weights from %s", self.weights_path)

    # --------------------------------------------------------- noise suppression
    def calibrate(self, background_audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
        """Teach ANS what the *background* sounds like (leak-free audio of the same sensor)."""
        clip = validate_and_fit(background_audio, sample_rate)
        with self._lock:
            calibrate_suppressor(self.ans, clip, self.preset)

    def reset_calibration(self) -> None:
        with self._lock:
            self.ans.reset()

    # ---------------------------------------------------------------- inference
    def predict_proba(self, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
        """Softmax probabilities, shape ``(4,)``."""
        return self._infer(audio_data, sample_rate)[0]

    def _infer(self, audio_data: np.ndarray, sample_rate: int):
        clip = validate_and_fit(audio_data, sample_rate)
        self._load()
        with self._lock:
            cleaned = dsp_chain(clip, self.ans if self.use_ans else None, self.preset)
        feats = log_mel_spectrogram(cleaned, SAMPLE_RATE)
        torch = self._torch
        try:
            with torch.inference_mode():
                x = torch.from_numpy(feats).unsqueeze(0).unsqueeze(0).to(self.device)
                probs = torch.softmax(self._model(x), dim=1)[0].cpu().numpy()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Inference failed: {exc}") from exc
        return probs.astype(np.float64), cleaned

    def predict(self, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> Dict[str, Any]:
        """Return a dict conforming to ``shared.schemas.InferenceOutput``.

        Raises ``ValueError`` for empty / non-1D / non-finite / too-short audio and
        ``RuntimeError`` if the weights are missing or inference fails.
        """
        probs, cleaned = self._infer(audio_data, sample_rate)
        class_id = int(np.argmax(probs))
        return {
            "class_id": class_id,
            "class_label": CLASS_LABELS[class_id],
            "confidence": round(float(probs[class_id]), 4),
            "peak_frequency_hz": round(dominant_frequency_hz(cleaned, SAMPLE_RATE), 2),
            "timestamp": _utc_timestamp(),
        }
