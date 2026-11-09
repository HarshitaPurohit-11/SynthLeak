"""Compact 4-class CNN for 128x128 log-Mel spectrograms (PyTorch)."""

from __future__ import annotations

from typing import Sequence

import torch
from torch import nn

from shared.constants import CLASS_LABELS, SPECTROGRAM_SHAPE

NUM_CLASSES: int = len(CLASS_LABELS)
DEFAULT_WIDTHS: tuple[int, ...] = (16, 32, 64, 96)


def _block(c_in: int, c_out: int, double: bool) -> nn.Sequential:
    layers: list[nn.Module] = [
        nn.Conv2d(c_in, c_out, kernel_size=3, padding=1, bias=False),
        nn.BatchNorm2d(c_out),
        nn.ReLU(inplace=True),
    ]
    if double:
        layers += [
            nn.Conv2d(c_out, c_out, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c_out),
            nn.ReLU(inplace=True),
        ]
    layers.append(nn.MaxPool2d(2))
    return nn.Sequential(*layers)


class LeakCNN(nn.Module):
    """Input ``(B, 1, 128, 128)`` in [0, 1]; output logits ``(B, 4)``.

    Four conv blocks (the first is a single conv to keep CPU cost low), global average
    pooling, dropout and a linear head. ~200k parameters; trains on a laptop CPU.
    """

    def __init__(self, num_classes: int = NUM_CLASSES, widths: Sequence[int] = DEFAULT_WIDTHS,
                 dropout: float = 0.3) -> None:
        super().__init__()
        blocks: list[nn.Module] = []
        c_in = 1
        for idx, c_out in enumerate(widths):
            blocks.append(_block(c_in, int(c_out), double=idx > 0))
            c_in = int(c_out)
        self.features = nn.Sequential(*blocks)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(dropout), nn.Linear(c_in, num_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.pool(self.features(x)))


def build_model(widths: Sequence[int] = DEFAULT_WIDTHS, dropout: float = 0.3) -> LeakCNN:
    return LeakCNN(NUM_CLASSES, widths, dropout)


def input_shape() -> tuple[int, int, int]:
    return (1, SPECTROGRAM_SHAPE[0], SPECTROGRAM_SHAPE[1])
