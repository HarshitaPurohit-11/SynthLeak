# Engineering Roles & Domain Ownership

The SynthLeak platform is structured across four primary engineering disciplines. Each domain maintains explicit directory boundaries and adheres to the canonical interfaces defined in [`CONTRACT.md`](../CONTRACT.md).

---

## 1. Acoustic Signal Processing & ML

- **Domain Scope:** `ml/`, `audio-engine/dsp/`
- **Focus Areas:**
  - 4th-order Butterworth bandpass filtering (100 Hz–10 kHz platform baseline, 500 Hz–9 kHz urban vibration preset).
  - Adaptive Noise Suppression (ANS) via spectral subtraction to attenuate stationary environmental interference.
  - Short-Time Fourier Transform (STFT) with Hann windowing (`N_FFT = 1024`, `HOP_LENGTH = 512`).
  - 128-bin Mel filterbank generation and Log-Mel spectrogram calculation (`SPECTROGRAM_SHAPE = (128, 128)`).
  - Convolutional Neural Network (CNN) architecture, dataset preparation, and cross-entropy training across four acoustic classes (`NORMAL_FLOW`, `AMBIENT_URBAN`, `PINHOLE_LEAK`, `CAVITATION_BURST`).
  - Standardized inference callable: `predict(audio_data: np.ndarray, sample_rate: int = 44100) -> dict`.
  - Dominant frequency extraction (Hz) and RMS signal level estimation.
- **Key Artifacts:** `ml/classifier.py`, `ml/model.py`, `ml/weights/`, `audio-engine/dsp/`, `ml/tests/`.
- **Interface Output:** Conforms to the ML Inference schema in [`CONTRACT.md`](../CONTRACT.md#4-ml-inference-interface).

---

## 2. Frontend & GIS Development

- **Domain Scope:** `frontend/`
- **Focus Areas:**
  - Modern React single-page dashboard with Tailwind CSS and modular component structure.
  - High-performance HTML5 Canvas / WebGL rolling waterfall spectrogram visualization (10–20 FPS).
  - Resilient WebSocket client connecting to `/ws/stream` with reconnection logic and message dispatch.
  - Interactive Leaflet.js GIS pipeline network map displaying pipeline geometries, sensor markers, operational statuses, and pinpointed leak locations.
  - Dynamic sound pressure level gauges (dBFS), frequency readouts, and classification confidence badges.
  - Real-time incident banner and notification center.
  - Work-order maintenance ticket modal connected to `POST /tickets`.
  - Demo controls enabling switching between live stream capture and canned scenario playback.
- **Key Artifacts:** `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/`.
- **Interface Input:** Consumes the WebSocket telemetry stream and REST endpoints in [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream).

---

## 3. Backend & Infrastructure

- **Domain Scope:** `backend/`, `audio-engine/capture.py`, containerization (`Dockerfile`, `docker-compose.yml`)
- **Focus Areas:**
  - Asynchronous FastAPI server implementing REST endpoints (`GET /health`, `GET /pipelines`, `GET /alerts`, `POST /tickets`).
  - High-concurrency WebSocket broadcaster streaming real-time spectrogram frames and alert events.
  - Hardware audio ingestion and lockless circular ring buffer management (`CLIP_SAMPLES = 65536`).
  - Non-blocking ML inference orchestration using thread pool executors (`asyncio.to_thread`).
  - Synthetic noise generation and scenario replay engine for offline testing and demos.
  - SQLite persistence layer managing pipelines, historical alert logs, and work-order records (`synthleak.db`).
  - Anomaly detection rule engine and ticket lifecycle manager.
  - Dual-sensor Time Difference of Arrival (TDoA) cross-correlation localization engine.
  - Multi-container Docker deployment and environment configuration.
- **Key Artifacts:** `backend/main.py`, `backend/routes/`, `backend/db/`, `audio-engine/capture.py`, `Dockerfile`.
- **Interface Output:** Implements and serves all endpoints and protocols in [`CONTRACT.md`](../CONTRACT.md).

---

## 4. Demo Production & Documentation

- **Domain Scope:** `demo/`, `data/`, `scripts/`
- **Focus Areas:**
  - Curating and generating representative acoustic audio datasets across all four classes:
    - Normal laminar pipe flow
    - Urban background ambient noise
    - High-frequency orifice pinhole leaks
    - Transient cavitation bursts and pressure surges
  - GeoJSON pipeline network fixtures with realistic spatial coordinates, valve locations, and sensor placements.
  - Root project `README.md` and presentation assets.
  - Automated API verification test harness (`scripts/test_api.py`).
  - End-to-end demo recordings, architectural diagrams, and user interface screenshots.
- **Key Artifacts:** `data/sample_audio/`, `scripts/test_api.py`, `demo/`, `README.md`.

---

## Domain Ownership Matrix

| Functional Area | Primary Engineering Discipline | Canonical Contract Reference |
|---|---|---|
| Audio Capture & Ring Buffering | Backend & Infrastructure | [`CONTRACT.md`](../CONTRACT.md#2-shared-audio-constants--configuration) |
| DSP Filtering & Noise Suppression | Acoustic Signal Processing & ML | [`CONTRACT.md`](../CONTRACT.md#2-shared-audio-constants--configuration) |
| Spectrogram Extraction & CNN Inference | Acoustic Signal Processing & ML | [`CONTRACT.md`](../CONTRACT.md#4-ml-inference-interface) |
| FastAPI REST & WebSocket Server | Backend & Infrastructure | [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream) |
| SQLite Database & Data Persistence | Backend & Infrastructure | [`CONTRACT.md`](../CONTRACT.md#7-database-schema--entity-definitions) |
| React UI & Leaflet GIS Map | Frontend & GIS Development | [`CONTRACT.md`](../CONTRACT.md#6-rest-api-interface) |
| HTML5 Canvas Waterfall Spectrogram | Frontend & GIS Development | [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream) |
| Work-Order Ticket Dispatch | Frontend & GIS (UI) / Backend & Infrastructure (API) | [`CONTRACT.md`](../CONTRACT.md#63-post-tickets) |
| Sample Audio & GeoJSON Fixtures | Demo Production & Documentation | [`CONTRACT.md`](../CONTRACT.md#61-get-pipelines) |
| Integration Testing & Demo Media | Demo Production & Documentation | [`CONTRACT.md`](../CONTRACT.md#6-rest-api-interface) |
| Containerization & Deployment | Backend & Infrastructure | [`docs/SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) |
