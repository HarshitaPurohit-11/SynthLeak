"""Validation pass: confusion matrix, accuracy vs SNR (ANS on/off), latency.

    python -m ml.evaluate [--n-test 150] [--n-snr 60] [--real-dir data/sample_audio]

Outputs in ml/reports/: metrics.json, metrics_summary.md, confusion_matrix.png,
accuracy_vs_snr.png. All numbers are measured here - nothing is hard-coded.
NOTE: the test data is SYNTHETIC unless --real-dir is given; say so on the slides.
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import time
from pathlib import Path

import numpy as np

from ml.classifier import LeakClassifier
from ml.preprocessing import _ROOT
from ml.training.synthetic import make_sample
from shared.constants import CLASS_LABELS, CLIP_SAMPLES, SAMPLE_RATE

logger = logging.getLogger("evaluate")
ML_DIR = _ROOT / "ml"
SNR_LEVELS = [20, 10, 5, 0, -5]
ALERT_CLASSES = (2, 3)


def _probs(clf: LeakClassifier, clip: np.ndarray, bg: np.ndarray, ans: bool) -> np.ndarray:
    clf.use_ans = ans
    clf.reset_calibration()
    if ans:
        clf.calibrate(bg)
    return clf.predict_proba(clip)


def _confusion(y_true, y_pred, k=4) -> np.ndarray:
    cm = np.zeros((k, k), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", default=None)
    ap.add_argument("--n-test", type=int, default=150, help="test clips per class")
    ap.add_argument("--n-snr", type=int, default=60, help="clips per class per SNR level")
    ap.add_argument("--n-latency", type=int, default=100)
    ap.add_argument("--seed", type=int, default=12345, help="different from the training seeds")
    ap.add_argument("--real-dir", default=None)
    ap.add_argument("--out", default=str(ML_DIR / "reports"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    clf = LeakClassifier(args.weights)
    clf._load()  # fail early with a clear message if weights are missing
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    names = [CLASS_LABELS[i] for i in range(4)]

    # 1) Main test set (mixed SNR) -> confusion matrix, with and without ANS
    logger.info("Main test set: %d clips per class", args.n_test)
    y_true, pred = [], {False: [], True: []}
    for cid in range(4):
        for _ in range(args.n_test):
            clip, bg = make_sample(cid, rng)
            y_true.append(cid)
            for ans in (False, True):
                pred[ans].append(int(np.argmax(_probs(clf, clip, bg, ans))))
    y_true = np.array(y_true)
    results: dict = {}
    for ans in (False, True):
        yp = np.array(pred[ans])
        cm = _confusion(y_true, yp)
        recall = cm.diagonal() / cm.sum(1).clip(min=1)
        precision = cm.diagonal() / cm.sum(0).clip(min=1)
        leak_mask = np.isin(y_true, ALERT_CLASSES)
        results["ans_on" if ans else "ans_off"] = {
            "accuracy": float((yp == y_true).mean()),
            "confusion_matrix": cm.tolist(),
            "per_class_recall": {names[i]: float(recall[i]) for i in range(4)},
            "per_class_precision": {names[i]: float(precision[i]) for i in range(4)},
            "alert_detection_recall": float(np.isin(yp[leak_mask], ALERT_CLASSES).mean()),
            "false_alarm_rate": float(np.isin(yp[~leak_mask], ALERT_CLASSES).mean()),
        }

    # 2) SNR sweep on the two alert classes
    logger.info("SNR sweep %s dB, %d clips per class per level", SNR_LEVELS, args.n_snr)
    sweep = {"snr_db": SNR_LEVELS, "ans_off": {"class_accuracy": [], "alert_recall": []},
             "ans_on": {"class_accuracy": [], "alert_recall": []}}
    for snr in SNR_LEVELS:
        stats = {False: [0, 0, 0], True: [0, 0, 0]}  # correct, alerted, total
        for cid in ALERT_CLASSES:
            for _ in range(args.n_snr):
                clip, bg = make_sample(cid, rng, snr_db=snr)
                for ans in (False, True):
                    p = int(np.argmax(_probs(clf, clip, bg, ans)))
                    stats[ans][0] += int(p == cid)
                    stats[ans][1] += int(p in ALERT_CLASSES)
                    stats[ans][2] += 1
        for ans, key in ((False, "ans_off"), (True, "ans_on")):
            sweep[key]["class_accuracy"].append(stats[ans][0] / stats[ans][2])
            sweep[key]["alert_recall"].append(stats[ans][1] / stats[ans][2])
    results["snr_sweep"] = sweep

    # 3) Latency of the full predict() path (validation + DSP + CNN + peak frequency)
    clf.use_ans = False
    clips = [make_sample(int(rng.integers(0, 4)), rng)[0] for _ in range(args.n_latency)]
    for c in clips[:5]:
        clf.predict(c)  # warm-up
    times = []
    for c in clips:
        t0 = time.perf_counter()
        clf.predict(c)
        times.append((time.perf_counter() - t0) * 1000.0)
    t = np.array(times)
    clip_seconds = CLIP_SAMPLES / SAMPLE_RATE
    results["latency_ms"] = {"mean": float(t.mean()), "p50": float(np.percentile(t, 50)),
                             "p95": float(np.percentile(t, 95)), "max": float(t.max()), "n": len(t),
                             "real_time_factor": float(t.mean() / 1000.0 / clip_seconds)}

    # 4) Optional: real recordings
    if args.real_dir:
        from ml.training.real_audio import load_real_clips
        real = load_real_clips(args.real_dir)
        if real:
            yt = np.array([c for _, c, _ in real])
            yp = np.array([int(np.argmax(_probs(clf, x, x, False))) for x, _, _ in real])
            results["real_audio"] = {"n_clips": len(real), "accuracy": float((yp == yt).mean()),
                                     "confusion_matrix": _confusion(yt, yp).tolist()}

    results["setup"] = {
        "dataset": "synthetic (ml/training/synthetic.py)" + (" + real recordings" if args.real_dir else ""),
        "test_seed": args.seed, "n_test_per_class": args.n_test, "n_snr_per_class": args.n_snr,
        "model_meta": clf.metadata,
        "machine": {"processor": platform.processor() or platform.machine(), "python": platform.python_version(),
                    "torch": clf._torch.__version__, "threads": int(clf._torch.get_num_threads())},
    }
    (out / "metrics.json").write_text(json.dumps(results, indent=2))
    _write_summary(out, results, names)
    _plots(out, results, names)
    logger.info("Wrote metrics.json, metrics_summary.md and plots to %s", out)


def _write_summary(out: Path, r: dict, names: list) -> None:
    a, b, lat, sw = r["ans_off"], r["ans_on"], r["latency_ms"], r["snr_sweep"]
    lines = [
        "# SynthLeak model validation (auto-generated by `python -m ml.evaluate`)",
        "",
        f"Data: {r['setup']['dataset']}. Synthetic results show the pipeline works; they are NOT a claim about real buried pipes.",
        "",
        f"- 4-class accuracy (mixed SNR): **{a['accuracy']:.1%}** (ANS off), **{b['accuracy']:.1%}** (ANS on)",
        f"- Alert detection recall (leak/burst flagged): {a['alert_detection_recall']:.1%} / {b['alert_detection_recall']:.1%}",
        f"- False alarm rate (normal/ambient flagged): {a['false_alarm_rate']:.1%} / {b['false_alarm_rate']:.1%}",
        f"- Latency per {CLIP_SAMPLES / SAMPLE_RATE:.2f} s clip: mean {lat['mean']:.1f} ms, p95 {lat['p95']:.1f} ms "
        f"(real-time factor {lat['real_time_factor']:.3f})",
        "",
        "| SNR (dB) | class acc, ANS off | class acc, ANS on | alert recall, ANS off | alert recall, ANS on |",
        "|---|---|---|---|---|",
    ]
    for i, snr in enumerate(sw["snr_db"]):
        lines.append(f"| {snr} | {sw['ans_off']['class_accuracy'][i]:.1%} | {sw['ans_on']['class_accuracy'][i]:.1%} | "
                     f"{sw['ans_off']['alert_recall'][i]:.1%} | {sw['ans_on']['alert_recall'][i]:.1%} |")
    (out / "metrics_summary.md").write_text("\n".join(lines) + "\n")


def _plots(out: Path, r: dict, names: list) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib missing - skipping plots")
        return
    cm = np.array(r["ans_off"]["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(4), names, rotation=30, ha="right")
    ax.set_yticks(range(4), names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix (synthetic test set, ANS off)")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=160)
    plt.close(fig)

    sw = r["snr_sweep"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(sw["snr_db"], sw["ans_off"]["alert_recall"], "o-", label="Alert recall, ANS off")
    ax.plot(sw["snr_db"], sw["ans_on"]["alert_recall"], "s-", label="Alert recall, ANS on")
    ax.plot(sw["snr_db"], sw["ans_off"]["class_accuracy"], "o--", label="Class accuracy, ANS off")
    ax.plot(sw["snr_db"], sw["ans_on"]["class_accuracy"], "s--", label="Class accuracy, ANS on")
    ax.set_xlabel("Leak-to-background SNR (dB)")
    ax.set_ylabel("Fraction correct")
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Leak / burst detection vs noise level")
    fig.tight_layout()
    fig.savefig(out / "accuracy_vs_snr.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
