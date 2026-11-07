# SynthLeak Engineering Guidelines

This document establishes the architectural standards, domain boundaries, code quality expectations, and consistency policies for the SynthLeak engineering team.

---

## 1. Domain Ownership & Responsibilities

The codebase is organized into four distinct engineering disciplines:

### Acoustic Signal Processing & ML
- **Scope:** `ml/`, `audio-engine/dsp/`
- **Focus:** Digital signal processing, Butterworth bandpass filtering, Adaptive Noise Suppression (ANS), STFT computation, 128-bin Mel spectrogram generation, 4-class CNN architecture, and model inference validation.
- **Contract Interface:** Exposes the inference callable specified in [`CONTRACT.md`](CONTRACT.md#4-ml-inference-interface).

### Frontend & GIS Development
- **Scope:** `frontend/`
- **Focus:** React dashboard, HTML5 Canvas/WebGL waterfall spectrogram visualization, WebSocket telemetry streaming, Leaflet.js pipeline GIS mapping, sound gauges, incident alerts, and work-order dispatch modal.
- **Contract Interface:** Consumes the WebSocket telemetry stream and REST endpoints specified in [`CONTRACT.md`](CONTRACT.md#5-real-time-dashboard-stream).

### Backend & Infrastructure
- **Scope:** `backend/`, `audio-engine/capture.py`, root containerization
- **Focus:** FastAPI asynchronous application, real-time WebSocket server, hardware audio capture and ring buffering, ML inference orchestration, SQLite storage, alert evaluation engine, TDoA cross-correlation localization, and Docker deployment.
- **Contract Interface:** Implements and serves all REST endpoints and WebSocket protocols specified in [`CONTRACT.md`](CONTRACT.md#6-rest-api-interface).

### Demo Production & Documentation
- **Scope:** `demo/`, `data/`, `scripts/`
- **Focus:** Curating acoustic sample datasets (normal flow, ambient urban, pinhole leaks, cavitation bursts), pipeline GeoJSON fixtures, API integration testing (`scripts/test_api.py`), project README, presentation materials, and demo recordings.

---

## 2. Core Architectural & Technical Standards

### Signal Processing & Terminology
- **Noise Suppression:** Always use the term **Adaptive Noise Suppression (ANS)**. Do not use "Active Noise Cancellation" (which refers to acoustic phase-inversion hardware).
- **Filter Cutoffs:** The platform architecture standard specifies a **100 Hz to 10 kHz** bandpass filter. The **500 Hz to 9 kHz** bandpass filter is an active tuning preset designed for high-vibration urban environments. The backend processes inference outputs agnostic of internal filter cutoffs.
- **Shared Parameters:** Never hardcode audio parameters or taxonomy indices. Always import constants from [`shared/constants.py`](shared/constants.py).

### Real-Time Streaming & Buffering
- **Audio Sliding Window:** Audio is ingested and processed in fixed chunks of **65,536 samples** ($128 \text{ frames} \times 512 \text{ hop}$ samples $\approx 1.486 \text{ s}$ at 44.1 kHz).
- **Non-Blocking Inference:** All CPU-bound DSP and ML classification tasks must be executed off the main FastAPI event loop (using `asyncio.to_thread` or thread pool executors) to guarantee uninterrupted WebSocket streaming.
- **WebSocket Frame Rate:** Real-time spectrogram frames are transmitted to the dashboard at **10 to 20 FPS** to prevent client-side render lag while delivering smooth waterfall visualization.

### Metric Integrity
- Do not hardcode static measurement claims (such as `"98.4% accuracy"` or `"0.8 mm pinhole diameter"`) into production payloads. All reported metrics must reflect actual model outputs or computed DSP values.
- Synthetic fixtures used for testing or offline demos must be explicitly designated with `"is_simulated": true`.

---

## 3. Code Quality & Standards

### Python (Backend, ML, Shared)
- Target Python 3.10+.
- Use explicit type hints for all function signatures and data structures.
- Validate all network and inter-module payloads using Pydantic models from [`shared/schemas.py`](shared/schemas.py).
- Use Python's standard `logging` module rather than raw `print()` statements in production services.
- Ensure database interactions in SQLite are managed with parameterized queries and explicit transactions.

### TypeScript / React (Frontend)
- Target modern React 18+ with functional components and custom hooks.
- Use strict TypeScript interfaces matching the data models in [`CONTRACT.md`](CONTRACT.md).
- Offload intensive spectrogram frame rendering to HTML5 Canvas or WebGL to preserve 60 FPS UI responsiveness.
- Provide user-visible connection state indicators with automatic reconnect logic for WebSocket streams.

---

## 4. Contract Governance

All inter-module communication is governed by [`CONTRACT.md`](CONTRACT.md). Any proposed modification to schemas, endpoints, or shared parameters must follow the formal change protocol detailed in [`CONTRIBUTING.md`](CONTRIBUTING.md#contract-change-protocol).

