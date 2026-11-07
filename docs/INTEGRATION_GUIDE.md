# Subsystem Integration & Mocking Guide

## 1. Decoupled Development Architecture

To enable concurrent engineering without blocking on incomplete components, SynthLeak utilizes a **contract-driven, stub-first integration pattern**:

```
[ Acoustic Signal Processing & ML ]  ─── Implements ───>  predict(audio_data) -> dict
          │                                                   │
          │ (Tested with synthetic sine/chirp arrays)         │ (Conforms to CONTRACT.md)
          ▼                                                   ▼
[ Backend & Infrastructure ]         <─── Mocks with ───   mock_classifier.py
          │                                                   │
          │ (Tested using mock payloads and replay streams)   │ (Streams CONTRACT.md format)
          ▼                                                   ▼
[ Frontend & GIS Development ]       <─── Consumes ─────   Mock WebSocket / Live Backend
```

---

## 2. Acoustic Signal Processing & ML: Isolated Testing

The ML module in `ml/` and `audio-engine/dsp/` can be fully exercised and validated without starting the FastAPI server or React UI.

### Testing Inference Locally
```python
import numpy as np
from shared.constants import CLIP_SAMPLES, SAMPLE_RATE
from ml.classifier import LeakClassifier

classifier = LeakClassifier(weights_path="ml/weights/leak_cnn.pt")

# Generate 1.486 sec synthetic 4.2 kHz pinhole leak tone
t = np.linspace(0, CLIP_SAMPLES / SAMPLE_RATE, CLIP_SAMPLES, endpoint=False)
synthetic_leak = 0.5 * np.sin(2 * np.pi * 4200 * t) + 0.05 * np.random.normal(0, 1, CLIP_SAMPLES)

result = classifier.predict(synthetic_leak, sample_rate=SAMPLE_RATE)
print("Inference Result:", result)

# Validate against canonical contract schema
from shared.schemas import InferenceOutput
validated = InferenceOutput(**result)
print("Schema Validation: SUCCESS!", validated.model_dump())
```

---

## 3. Backend: Mocking ML Inference

During early development or prior to final model training, the backend pipeline runs against a lightweight mock classifier (`backend/mock_classifier.py`) that returns conforming payloads:

```python
import time
from datetime import datetime, timezone
import numpy as np
from shared.constants import CLASS_PINHOLE_LEAK, CLASS_LABELS
from shared.schemas import InferenceOutput

class MockLeakClassifier:
    def predict(self, audio_data: np.ndarray, sample_rate: int = 44100) -> dict:
        # Inspect peak frequency via FFT
        fft_vals = np.abs(np.fft.rfft(audio_data))
        freqs = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
        peak_idx = np.argmax(fft_vals)
        peak_freq = float(freqs[peak_idx])
        
        # Heuristic classification for pipeline testing
        if peak_freq > 3000.0:
            cid = CLASS_PINHOLE_LEAK
        else:
            cid = 0
            
        return {
            "class_id": cid,
            "class_label": CLASS_LABELS[cid],
            "confidence": 0.9450,
            "peak_frequency_hz": round(peak_freq, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
```

This allows the backend engineering team to implement the real-time ring buffer, SQLite store, alert rules, and WebSocket broadcaster with zero dependencies on finalized model weights.

---

## 4. Frontend: Independent UI Development

The React dashboard and Canvas waterfall spectrogram can be developed and styled independently of the live Python backend:

### Option A: Standalone Mock WebSocket Server
A lightweight mock script can stream `shared/examples/websocket_detection.json` frames at 15 FPS:
```bash
python scripts/mock_ws_server.py --port 8000
```

### Option B: Local JSON Fixtures
Load `shared/examples/pipeline_geojson.json` and `shared/examples/alert_response.json` into component mock states to verify:
- The Leaflet pipeline map with colored status polylines.
- Sound level meters and frequency readouts.
- Work-order creation modal.

---

## 5. End-to-End API Test Harness

Integration verification is performed via `scripts/test_api.py`:

1. **Verify Backend Health:** `GET /health` returns `200 OK`.
2. **Verify Pipelines:** `GET /pipelines` returns valid GeoJSON features.
3. **Trigger Alert & Check Logs:** `GET /alerts` returns log entries matching `CONTRACT.md`.
4. **Create Work Order:** `POST /tickets` creates a valid ticket with status `OPEN`.
5. **Listen to WebSocket:** Connects to `ws://localhost:8000/ws/stream` and validates frames against `SpectrogramFrameMessage`.

---

## 6. Subsystem Integration Checklist

| Step | Milestone | Verification Target |
|---|---|---|
| 1 | Shared constants imported | All modules use `shared.constants` without hardcoded magic numbers |
| 2 | Model weights exported | `ml/classifier.py` executes `predict()` returning `InferenceOutput` |
| 3 | Backend attaches ML classifier | Swaps `mock_classifier` for `ml.classifier` |
| 4 | Dashboard connects to WebSocket | Canvas renders continuous waterfall frames at 10–20 FPS |
| 5 | Ticket dispatch operational | Frontend modal creates row in SQLite `work_order_tickets` |
| 6 | Integration test passes | `python scripts/test_api.py` exits with code 0 |
| 7 | Containerized launch | `docker compose up --build` boots all services |
