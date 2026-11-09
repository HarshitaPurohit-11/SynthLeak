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

---

## Quick start (Member 1 deliverables)

```bash
pip install -r requirements.txt -r ml/requirements-ml.txt
python scripts/validate_contracts.py              # shared contract still passes
pytest ml/tests audio-engine/tests -v             # DSP + ML tests
python -m ml.demo_predict                         # one synthetic example per class
python -m ml.training.train                       # retrain (about 5-20 min on CPU); --quick for a smoke run
python -m ml.evaluate                             # confusion matrix, SNR sweep, latency -> ml/reports/
python -m ml.export_demo_clips                    # synthetic WAVs for scenario replay
```

`ml/weights/leak_cnn.pt` (about 0.85 MB) is committed, so `LeakClassifier()` works immediately.

## What is where

| Path | Purpose |
|---|---|
| `audio-engine/dsp/filters.py` | 4th-order Butterworth bandpass (100 Hz-10 kHz default, 500 Hz-9 kHz `urban` preset), Adaptive Noise Suppression |
| `audio-engine/dsp/spectrogram.py` | Hann STFT, 128-bin Slaney Mel filterbank (100 Hz-10 kHz), dB scaling, dominant frequency, dBFS |
| `ml/preprocessing.py` | Input validation (exact CONTRACT.md 4.4 errors), resampling, DSP chain |
| `ml/model.py` | `LeakCNN`, about 209k parameters, input `(B, 1, 128, 128)` |
| `ml/classifier.py` | `LeakClassifier.predict()` returning the `InferenceOutput` dict |
| `ml/training/` | `synthetic.py` (data generator), `dataset.py`, `real_audio.py`, `train.py` |
| `ml/evaluate.py` | Validation pass producing `ml/reports/*` |

## Design decisions to know for judging Q&A
- **128 x 128 input:** 65 536 samples with centred STFT frames give 129 frames; the first 128 are kept (`SPECTROGRAM_SHAPE`).
- **Fixed dB window, not per-clip normalisation:** absolute loudness stays a cue (a loud leak differs from a quiet hum).
- **ANS needs a background profile.** A pinhole leak is a *stationary* hiss, so blind noise estimation would remove the
  leak with the noise. ANS therefore subtracts a profile learned from leak-free audio (`LeakClassifier.calibrate`) and
  does nothing until calibrated. It is applied to half the training samples so the model works with ANS on or off.
- **`peak_frequency_hz`** is the maximum of the time-averaged, lightly smoothed spectrum inside the filter band. For a
  broadband hiss this value wanders within the leak band, and for a burst with a low thump it can sit at low frequency.
  Treat it as an indicator, not a precise measurement.
- **Leak position** is not computed here; the backend's two-sensor cross-correlation provides it.

## Validation results and their limits
`ml/reports/metrics_summary.md` (generated by `python -m ml.evaluate`) holds the current numbers. On the synthetic test
set (seed 12345, separate from the training seeds) the committed model reaches about 99% 4-class accuracy, 100% alert
recall and 0% false alarms, with about 14 ms mean latency per 1.49 s clip on a single CPU thread.

**These are synthetic-data results.** The synthetic hiss (1.5-8 kHz) and the background (mostly below about 1.2 kHz)
barely overlap in frequency, which is why accuracy stays near 100% even at -5 dB. Real buried pipes, soil attenuation
and real microphones will be harder. Say "validated on synthetic data" on the slides, and add real recordings
(`data/sample_audio`, `--real-dir`) to get honest real-world numbers.
