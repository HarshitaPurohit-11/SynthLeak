# Acoustic Signal Processing & ML

This module houses the digital signal processing (DSP) algorithms, feature extraction pipelines, neural network architecture, and inference callable for classifying acoustic pipeline emissions.

---

## Responsibilities

- **Bandpass Filtering:** 4th-order Butterworth bandpass filtering (100 Hz–10 kHz default, 500 Hz–9 kHz urban vibration preset) to isolate hydraulic acoustic signatures.
- **Adaptive Noise Suppression (ANS):** Spectral subtraction estimating the background noise floor to eliminate environmental interference.
- **Feature Extraction:** Hann-window STFT computing 128-bin Mel spectrograms (`N_FFT = 1024`, `HOP_LENGTH = 512`, `N_MELS = 128`).
- **CNN Classifier:** 4-class convolutional neural network classifying inputs into:
  - `0`: `NORMAL_FLOW`
  - `1`: `AMBIENT_URBAN`
  - `2`: `PINHOLE_LEAK`
  - `3`: `CAVITATION_BURST`
- **Inference Callable:** Exposes `predict(audio_data: np.ndarray, sample_rate: int = 44100) -> dict` returning the schema defined in `CONTRACT.md`.
- **Spectral Metrics:** Computes the dominant acoustic frequency in Hz and RMS signal power.

---

## Directory Layout

```
ml/
├── classifier.py           # Production inference callable conforming to CONTRACT.md
├── model.py                # PyTorch/TensorFlow CNN architecture definition
├── preprocessing.py        # Normalization, DC removal, and tensor formatting
├── training/               # Model training and dataset loaders
│   ├── dataset.py          # Audio dataset loaders and data augmentation
│   └── train.py            # Training loop, loss functions, and checkpoints
├── weights/                # Serialized model weights (.pt, .onnx)
└── tests/                  # Model unit tests and metric validation
```

---

## Development & Testing

### Running Tests Locally
```bash
pytest ml/tests/ -v
```

### Verifying Inference Output
```python
import numpy as np
from shared.constants import CLIP_SAMPLES, SAMPLE_RATE
from shared.schemas import InferenceOutput
from ml.classifier import LeakClassifier

classifier = LeakClassifier()
sample_audio = np.zeros(CLIP_SAMPLES, dtype=np.float32)
output = classifier.predict(sample_audio, sample_rate=SAMPLE_RATE)

# Verify against shared contract schema
validated = InferenceOutput(**output)
print("Contract validation passed:", validated.model_dump())
```

---

## Interface Contracts
- **Callable Specification:** Matches [`CONTRACT.md`](../CONTRACT.md#4-ml-inference-interface).
- **Shared Parameters:** Uses audio constants from [`shared/constants.py`](../shared/constants.py).

