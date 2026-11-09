"""Optional loader for REAL recorded clips (e.g. Member 4's ``data/sample_audio``).

A WAV is assigned to a class from its folder name or file name keywords:
  normal/flow -> NORMAL_FLOW      ambient/traffic/urban/silence/noise -> AMBIENT_URBAN
  leak/pinhole/hiss/bottle        -> PINHOLE_LEAK
  burst/cavitation/hammer/pump    -> CAVITATION_BURST
Unmatched files are skipped (and reported). Clips are mono, resampled to 44.1 kHz and
chopped into non-overlapping ``CLIP_SAMPLES`` windows (last partial window dropped).
"""

from __future__ import annotations

import logging
from math import gcd
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from shared.constants import (
    CLASS_AMBIENT_URBAN,
    CLASS_CAVITATION_BURST,
    CLASS_NORMAL_FLOW,
    CLASS_PINHOLE_LEAK,
    CLIP_SAMPLES,
    SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

# Order matters: more specific keywords first.
KEYWORDS: List[Tuple[str, int]] = [
    ("cavitation", CLASS_CAVITATION_BURST), ("burst", CLASS_CAVITATION_BURST),
    ("hammer", CLASS_CAVITATION_BURST), ("pump", CLASS_CAVITATION_BURST),
    ("pinhole", CLASS_PINHOLE_LEAK), ("leak", CLASS_PINHOLE_LEAK),
    ("hiss", CLASS_PINHOLE_LEAK), ("bottle", CLASS_PINHOLE_LEAK),
    ("ambient", CLASS_AMBIENT_URBAN), ("traffic", CLASS_AMBIENT_URBAN),
    ("urban", CLASS_AMBIENT_URBAN), ("silence", CLASS_AMBIENT_URBAN), ("noise", CLASS_AMBIENT_URBAN),
    ("normal", CLASS_NORMAL_FLOW), ("flow", CLASS_NORMAL_FLOW),
]


def infer_class(path: Path, root: Path) -> int | None:
    name = "/".join(path.relative_to(root).parts).lower()
    for kw, cid in KEYWORDS:
        if kw in name:
            return cid
    return None


def _read_mono(path: Path) -> np.ndarray:
    sr, data = wavfile.read(str(path))
    x = data.astype(np.float32)
    if data.dtype == np.int16:
        x /= 32768.0
    elif data.dtype == np.int32:
        x /= 2147483648.0
    elif data.dtype == np.uint8:
        x = (x - 128.0) / 128.0
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SAMPLE_RATE:
        g = gcd(int(sr), SAMPLE_RATE)
        x = resample_poly(x, SAMPLE_RATE // g, int(sr) // g).astype(np.float32)
    return x


def load_real_clips(root: str | Path) -> List[Tuple[np.ndarray, int, str]]:
    """Return ``[(clip, class_id, source_file), ...]``. Empty list if folder is missing."""
    root = Path(root)
    out: List[Tuple[np.ndarray, int, str]] = []
    if not root.is_dir():
        logger.warning("Real audio folder %s not found - skipping", root)
        return out
    for wav in sorted(root.rglob("*.wav")):
        cid = infer_class(wav, root)
        if cid is None:
            logger.warning("Skipping %s: cannot infer class from its name", wav)
            continue
        try:
            x = _read_mono(wav)
        except Exception as exc:  # noqa: BLE001 - report and continue
            logger.warning("Skipping %s: %s", wav, exc)
            continue
        for s in range(0, x.size - CLIP_SAMPLES + 1, CLIP_SAMPLES):
            out.append((x[s:s + CLIP_SAMPLES].copy(), cid, str(wav)))
        if x.size < CLIP_SAMPLES:
            logger.warning("%s shorter than %d samples; skipped", wav, CLIP_SAMPLES)
    return out
