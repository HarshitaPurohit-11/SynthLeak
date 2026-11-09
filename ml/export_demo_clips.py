"""Write synthetic demo WAVs for scenario replay / testing (no hardware needed).

    python -m ml.export_demo_clips            # -> ml/reports/demo_clips/*.wav (git-ignored)

Files: one clip per class plus ``scenario_baseline_leak_burst.wav`` (traffic baseline ->
pinhole leak -> burst), the audio counterpart of the dashboard's demo replay. These are
SYNTHETIC - label them as such in any demo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from ml.preprocessing import _ROOT
from ml.training.synthetic import make_sample
from shared.constants import CLASS_LABELS, SAMPLE_RATE


def _write(path: Path, x: np.ndarray) -> None:
    wavfile.write(path, SAMPLE_RATE, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(_ROOT / "ml" / "reports" / "demo_clips"))
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    for cid, label in CLASS_LABELS.items():
        clip = np.concatenate([make_sample(cid, rng, snr_db=12.0)[0] for _ in range(4)])
        _write(out / f"synthetic_{label.lower()}.wav", clip)
    parts = ([make_sample(1, rng)[0] for _ in range(6)] + [make_sample(2, rng, snr_db=8.0)[0] for _ in range(8)]
             + [make_sample(3, rng, snr_db=6.0)[0] for _ in range(4)])
    _write(out / "scenario_baseline_leak_burst.wav", np.concatenate(parts))
    print(f"Wrote {len(CLASS_LABELS) + 1} WAV files to {out}")


if __name__ == "__main__":
    main()
