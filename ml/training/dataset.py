"""Dataset construction (torch-free so it can be tested anywhere)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from ml.preprocessing import AdaptiveNoiseSuppressor, calibrate_suppressor, extract_features
from ml.training.synthetic import make_sample
from shared.constants import CLASS_LABELS

logger = logging.getLogger(__name__)
NUM_CLASSES = len(CLASS_LABELS)


def build_synthetic_dataset(
    n_per_class: int,
    seed: int,
    snr_range: Tuple[float, float] = (-3.0, 20.0),
    ans_fraction: float = 0.5,
    verbose: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """``X`` float32 ``(N, 128, 128)`` log-Mel images and ``y`` int64 labels, shuffled.

    ``ans_fraction`` of the samples go through Adaptive Noise Suppression calibrated on an
    independent background clip, so the CNN works with the dashboard's ANS toggle on or off.
    """
    rng = np.random.default_rng(seed)
    total = n_per_class * NUM_CLASSES
    X = np.empty((total, 128, 128), dtype=np.float32)
    y = np.empty(total, dtype=np.int64)
    i = 0
    for cid in range(NUM_CLASSES):
        for _ in range(n_per_class):
            clip, bg = make_sample(cid, rng, snr_range=snr_range)
            ans = None
            if rng.random() < ans_fraction:
                ans = AdaptiveNoiseSuppressor()
                calibrate_suppressor(ans, bg)
            X[i] = extract_features(clip, ans)
            y[i] = cid
            i += 1
            if verbose and i % 400 == 0:
                logger.info("  generated %d/%d samples", i, total)
    perm = rng.permutation(total)
    return X[perm], y[perm]


def build_real_dataset(real_dir: str | Path) -> Tuple[np.ndarray, np.ndarray]:
    from ml.training.real_audio import load_real_clips

    clips = load_real_clips(real_dir)
    if not clips:
        return np.empty((0, 128, 128), np.float32), np.empty(0, np.int64)
    X = np.stack([extract_features(c) for c, _, _ in clips]).astype(np.float32)
    y = np.array([cid for _, cid, _ in clips], dtype=np.int64)
    return X, y


def load_or_build(cache_path: Optional[str | Path], **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """Cache synthetic datasets in ``.npz`` (keyed by the kwargs) to avoid regeneration."""
    key = "|".join(f"{k}={kwargs[k]}" for k in sorted(kwargs))
    if cache_path:
        cache_path = Path(cache_path)
        if cache_path.exists():
            blob = np.load(cache_path, allow_pickle=False)
            if str(blob["key"]) == key:
                logger.info("Loaded cached dataset %s", cache_path)
                return blob["X"], blob["y"]
    X, y = build_synthetic_dataset(**kwargs)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache_path, X=X, y=y, key=np.array(key))
    return X, y
