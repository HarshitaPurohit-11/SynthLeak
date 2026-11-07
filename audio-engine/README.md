# Audio Engine

The audio engine provides acoustic data acquisition and digital signal processing routines, bridging physical audio sensors (or simulation files) to feature tensors for neural network inference and WebSocket distribution.

---

## Signal Flow Architecture

```
[ Microphone / WAV Stream ]
           │
           ▼
[ audio-engine/capture.py ] (Backend & Infrastructure)
   - Circular Ring Buffer (65,536 samples @ 44.1 kHz)
   - Lockless read/write sliding window
           │
           ▼
[ audio-engine/dsp/filters.py ] (Acoustic Signal Processing & ML)
   - 4th-order Butterworth Bandpass Filter (100 Hz - 10 kHz default)
   - Adaptive Spectral Subtraction (Noise Suppression)
           │
           ▼
[ audio-engine/dsp/spectrogram.py ] (Acoustic Signal Processing & ML)
   - Hann-window STFT (N_FFT=1024, HOP=512)
   - Mel-scale Filterbank (N_MELS=128)
           │
           ├───────────────────────────────┐
           ▼                               ▼
[ CNN Classification Input (128x128) ] [ WebSocket Stream Frame (128 bins) ]
   (Handed to ml/classifier.py)            (Streamed to Frontend Dashboard)
```

---

## Component Boundaries

- **`audio-engine/dsp/`:** Owned by the **Acoustic Signal Processing & ML** team.
  - Contains core mathematical implementations: Butterworth bandpass filtering, spectral subtraction, Mel filterbanks, and dominant frequency calculations.
  - Free from network, HTTP, or WebSocket dependencies.
- **`audio-engine/capture.py`:** Owned by the **Backend & Infrastructure** team.
  - Implements hardware audio ingestion, scenario audio loaders, and the thread-safe circular ring buffer.

---

## Shared Parameters
- `SAMPLE_RATE = 44100` Hz
- `N_FFT = 1024` samples
- `HOP_LENGTH = 512` samples
- `N_MELS = 128` Mel frequency bins
- `CLIP_SAMPLES = 65536` samples (~1.486 sec)

All parameters are imported directly from [`shared/constants.py`](../shared/constants.py).

