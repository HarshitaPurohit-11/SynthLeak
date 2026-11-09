"""Run the classifier on a WAV file or on the built-in synthetic examples.

    python -m ml.demo_predict                       # 4 synthetic examples, one per class
    python -m ml.demo_predict path/to/clip.wav      # slide a 1.49 s window over a recording
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from ml.classifier import LeakClassifier
from ml.preprocessing import validate_and_fit
from ml.training.real_audio import _read_mono
from ml.training.synthetic import make_sample
from pathlib import Path
from shared.constants import CLASS_LABELS, CLIP_SAMPLES
from shared.schemas import InferenceOutput


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--ans", action="store_true", help="enable Adaptive Noise Suppression (calibrates on the first window)")
    args = ap.parse_args()
    clf = LeakClassifier(use_ans=args.ans)
    if args.wav:
        x = _read_mono(Path(args.wav))
        windows = [x[s:s + CLIP_SAMPLES] for s in range(0, max(1, x.size - CLIP_SAMPLES + 1), CLIP_SAMPLES)]
        if args.ans:
            clf.calibrate(windows[0])
        for i, w in enumerate(windows):
            out = InferenceOutput(**clf.predict(validate_and_fit(w))).model_dump()
            print(f"window {i:3d}: {json.dumps(out)}")
        return
    rng = np.random.default_rng(99)
    for cid, label in CLASS_LABELS.items():
        clip, bg = make_sample(cid, rng, snr_db=10.0)
        if args.ans:
            clf.calibrate(bg)
        out = InferenceOutput(**clf.predict(clip)).model_dump()
        print(f"true={label:17s} -> {json.dumps(out)}")


if __name__ == "__main__":
    main()
