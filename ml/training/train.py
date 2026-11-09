"""Train the LeakCNN.

    python -m ml.training.train                 # default: ~3-8 min on a laptop CPU
    python -m ml.training.train --quick         # 1-2 min smoke run
    python -m ml.training.train --real-dir data/sample_audio   # also use real recordings

Writes ``ml/weights/leak_cnn.pt`` (commit this small file so teammates can run inference).
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import time
from pathlib import Path

import numpy as np

from ml.preprocessing import _ROOT  # also puts the repo + audio-engine on sys.path
from ml.training.dataset import build_real_dataset, load_or_build
from shared.constants import CLASS_LABELS, N_FFT, N_MELS, HOP_LENGTH, SAMPLE_RATE

logger = logging.getLogger("train")
ML_DIR = _ROOT / "ml"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n-per-class", type=int, default=600, help="training clips per class")
    p.add_argument("--val-per-class", type=int, default=100)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=2e-3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ans-fraction", type=float, default=0.5)
    p.add_argument("--real-dir", type=str, default=None, help="folder of real WAV clips (optional)")
    p.add_argument("--device", type=str, default="auto", help="auto | cpu | cuda")
    p.add_argument("--out", type=str, default=str(ML_DIR / "weights" / "leak_cnn.pt"))
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--quick", action="store_true", help="tiny run to check the pipeline end-to-end")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.quick:
        args.n_per_class, args.val_per_class, args.epochs = 120, 40, 4

    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    from ml.model import DEFAULT_WIDTHS, build_model

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    logger.info("Device: %s | torch %s", device, torch.__version__)

    cache_dir = ML_DIR / "data_cache"
    tr_cache = None if args.no_cache else cache_dir / f"train_{args.n_per_class}_{args.seed}.npz"
    va_cache = None if args.no_cache else cache_dir / f"val_{args.val_per_class}_{args.seed + 1}.npz"
    t0 = time.time()
    logger.info("Building synthetic training set (%d clips/class)...", args.n_per_class)
    X_tr, y_tr = load_or_build(tr_cache, n_per_class=args.n_per_class, seed=args.seed,
                               ans_fraction=args.ans_fraction)
    X_va, y_va = load_or_build(va_cache, n_per_class=args.val_per_class, seed=args.seed + 1,
                               ans_fraction=args.ans_fraction)
    n_real = 0
    if args.real_dir:
        Xr, yr = build_real_dataset(args.real_dir)
        n_real = len(yr)
        if n_real:
            rng = np.random.default_rng(args.seed)
            idx = rng.permutation(n_real)
            cut = max(1, int(0.8 * n_real)) if n_real > 1 else 1
            X_tr = np.concatenate([X_tr, Xr[idx[:cut]]])
            y_tr = np.concatenate([y_tr, yr[idx[:cut]]])
            if n_real > cut:
                X_va = np.concatenate([X_va, Xr[idx[cut:]]])
                y_va = np.concatenate([y_va, yr[idx[cut:]]])
            logger.info("Added %d real clips (%d train / %d val)", n_real, cut, n_real - cut)
        else:
            logger.warning("No usable real clips found in %s", args.real_dir)
    logger.info("Data ready in %.1fs: train %s, val %s", time.time() - t0, X_tr.shape, X_va.shape)

    def to_t(X):
        return torch.from_numpy(X).unsqueeze(1)  # (N,1,128,128)

    tr_loader = DataLoader(TensorDataset(to_t(X_tr), torch.from_numpy(y_tr)),
                           batch_size=args.batch_size, shuffle=True, drop_last=True)
    va_x, va_y = to_t(X_va), torch.from_numpy(y_va)

    model = build_model().to(device)
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("LeakCNN parameters: %d", n_params)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optim = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(optim, max_lr=args.lr, epochs=args.epochs,
                                                steps_per_epoch=len(tr_loader))

    def augment(xb: "torch.Tensor") -> "torch.Tensor":
        shifts = torch.randint(0, xb.shape[-1], (xb.shape[0],)).tolist()
        xb = torch.stack([torch.roll(xb[i], shifts[i], dims=-1) for i in range(xb.shape[0])])
        return (xb + 0.04 * torch.randn(xb.shape[0], 1, 1, 1, device=xb.device)).clamp_(0.0, 1.0)

    def evaluate() -> tuple[float, float]:
        model.eval()
        correct, loss_sum = 0, 0.0
        with torch.no_grad():
            for i in range(0, len(va_x), 256):
                xb, yb = va_x[i:i + 256].to(device), va_y[i:i + 256].to(device)
                out = model(xb)
                loss_sum += criterion(out, yb).item() * len(yb)
                correct += (out.argmax(1) == yb).sum().item()
        return correct / len(va_x), loss_sum / len(va_x)

    best_acc, best_state, history = -1.0, None, []
    t_train = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        running, seen, t_ep = 0.0, 0, time.time()
        for xb, yb in tr_loader:
            xb, yb = augment(xb).to(device), yb.to(device)
            optim.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optim.step()
            sched.step()
            running += loss.item() * len(yb)
            seen += len(yb)
        val_acc, val_loss = evaluate()
        history.append({"epoch": epoch, "train_loss": running / seen, "val_loss": val_loss, "val_acc": val_acc})
        logger.info("epoch %2d/%d  train_loss %.4f  val_loss %.4f  val_acc %.4f  (%.1fs)",
                    epoch, args.epochs, running / seen, val_loss, val_acc, time.time() - t_ep)
        if val_acc >= best_acc:
            best_acc = val_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "classes": {str(k): v for k, v in CLASS_LABELS.items()},
        "sample_rate": int(SAMPLE_RATE), "n_fft": int(N_FFT), "hop_length": int(HOP_LENGTH), "n_mels": int(N_MELS),
        "best_val_acc": float(best_acc),
        "epochs": int(args.epochs), "n_per_class": int(args.n_per_class), "n_real_clips": int(n_real),
        "ans_fraction": float(args.ans_fraction), "seed": int(args.seed),
        "data": "synthetic" + (" + real recordings" if n_real else ""),
        "params": int(n_params), "torch": str(torch.__version__), "python": platform.python_version(),
        "trained_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    torch.save({"state_dict": best_state,
                "config": {"widths": list(DEFAULT_WIDTHS), "dropout": 0.3},
                "meta": meta}, out_path)
    reports = ML_DIR / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "training_history.json").write_text(json.dumps({"meta": meta, "history": history}, indent=2))
    logger.info("Saved %s (best val acc %.4f, %.1fs total training)", out_path, best_acc, time.time() - t_train)
    logger.info("Next: python -m ml.evaluate")


if __name__ == "__main__":
    main()
