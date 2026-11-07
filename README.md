# SynthLeak

**Real-Time Acoustic Pipeline Leak Detection and Localization Platform**

---

## 1. Project Overview

SynthLeak is an intelligent acoustic monitoring and incident localization platform designed for municipal water distribution infrastructure.

Water utilities globally lose up to 30% of treated drinking water to non-revenue water (NRW) losses caused by concealed pipe wall breaches, pinhole orifices, and cavitation damage. Traditional detection relies on periodic manual acoustic surveys with ground microphones or delayed volumetric mass balances that fail to pinpoint leaks before catastrophic pipe bursts occur.

SynthLeak provides a continuous, automated sensing pipeline:
1. Captures acoustic pipe wall emissions at 44.1 kHz.
2. Applies digital signal processing (4th-order Butterworth bandpass filtering and Adaptive Noise Suppression via spectral subtraction).
3. Computes continuous Short-Time Fourier Transform (STFT) 128-bin Mel spectrograms.
4. Classifies acoustic signatures using a 4-class convolutional neural network (`NORMAL_FLOW`, `AMBIENT_URBAN`, `PINHOLE_LEAK`, `CAVITATION_BURST`).
5. Computes Time Difference of Arrival (TDoA) cross-correlation between dual-sensor pairs to locate leaks along pipe chainage.
6. Streams live waterfall spectrograms and instantaneous anomaly alerts over WebSockets to an operator GIS dashboard (React & Leaflet.js) with integrated work-order dispatch.

---

## 2. Technology Stack

| Domain | Technologies | Purpose |
|---|---|---|
| **Audio Acquisition & DSP** | NumPy, SciPy Signal, SoundDevice / PyAudio | Circular ring buffering, Butterworth filtering, Adaptive Noise Suppression |
| **Acoustic ML Inference** | PyTorch / ONNX, Librosa | 4-class CNN acoustic classifier, 128-bin Mel spectrogram tensor extraction |
| **Backend API & Streaming** | Python 3.10+, FastAPI, Uvicorn, WebSockets | Asynchronous REST endpoints, real-time WebSocket distribution, alert evaluation |
| **Data Persistence** | SQLite 3 (`synthleak.db`), SQLAlchemy, aiosqlite | Relational storage for pipelines, sensor telemetry logs, alerts, and work orders |
| **Operator Dashboard** | React 18, TypeScript, Tailwind CSS, Vite | Responsive management console, incident management modals |
| **Visualization & GIS** | HTML5 2D Canvas / WebGL, Leaflet.js | High-fps rolling waterfall spectrogram, interactive GIS pipeline mapping |
| **Deployment & Tooling** | Docker, Docker Compose, Pytest, HTTPX | Containerized execution, automated contract validation, API test harness |

---

## 3. Prerequisites

- **Python:** Version 3.10 or higher.
- **Node.js:** Version 18 or higher (required for frontend dashboard development).
- **Git:** Version 2.30 or higher.
- **Docker & Docker Compose:** (Optional) Required for containerized deployment.

---

## 4. Local Environment Setup

Clone the repository and create an isolated Python virtual environment:

```bash
# Enter the project root directory
cd SynthLeak

# Create Python virtual environment
python -m venv venv

# Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate
```

---

## 5. Dependency Installation

Install the backend, DSP, database, and testing dependencies:

```bash
# Upgrade pip to latest version
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

---

## 6. Backend Startup Instructions

Once the functional backend entry point is implemented, launch the FastAPI server locally:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Documentation (Swagger):** `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc):** `http://localhost:8000/redoc`
- **Health Check Endpoint:** `http://localhost:8000/health`
- **Real-Time WebSocket Stream:** `ws://localhost:8000/ws/stream`

*(Note: The server will be available once Phase 3 functional backend development is initiated).*

---

## 7. Docker Startup Instructions

To build and run the backend inside a containerized environment with persistent volume storage for SQLite:

### Using Docker Compose
```bash
# Build and start the backend container in detached mode
docker compose up --build -d

# View container logs
docker compose logs -f backend

# Stop the container
docker compose down
```

### Using Standalone Docker Build
```bash
# Build the backend image from the repository root
docker build -f backend/Dockerfile -t synthleak-backend .

# Run container with mapped port and data volume
docker run -d -p 8000:8000 -v synthleak-data:/app/data --name synthleak-app synthleak-backend
```

---

## 8. API Testing Instructions

SynthLeak includes an automated test harness ([`scripts/test_api.py`](scripts/test_api.py)) and contract verification suite ([`scripts/validate_contracts.py`](scripts/validate_contracts.py)).

### 1. Offline Contract & Schema Verification (Runs Immediately)
Validates all canonical JSON examples against the Pydantic v2 schemas:
```bash
python scripts/validate_contracts.py
```

### 2. API Test Harness
Runs offline fixture verification and probes the live backend server:
```bash
# Auto-detects live server or falls back to offline contract testing:
python scripts/test_api.py

# Force offline validation mode only:
python scripts/test_api.py --offline-only

# Specify custom backend host:
python scripts/test_api.py --url http://127.0.0.1:8000
```

---

## 9. Documentation References

- **Canonical Interface Contract:** [`CONTRACT.md`](CONTRACT.md) — The single authoritative specification for all schemas, endpoints, and constants.
- **Engineering Guidelines:** [`PROJECT_GUIDELINES.md`](PROJECT_GUIDELINES.md) — Architectural principles, domain boundaries, and coding standards.
- **Developer Contribution & Git Workflow:** [`CONTRIBUTING.md`](CONTRIBUTING.md) — Git rules, review checklist, and contract change protocol.
- **System Architecture:** [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) — Signal chain, threading model, and TDoA localization.
- **API & Protocol Specifications:** [`docs/API_SPECIFICATION.md`](docs/API_SPECIFICATION.md) — Complete REST and WebSocket payload definitions.
- **Data Formats & Serialization:** [`docs/DATA_FORMATS.md`](docs/DATA_FORMATS.md) — Audio tensors, GeoJSON models, and SQLite DDL.
- **Integration & Mocking Guide:** [`docs/INTEGRATION_GUIDE.md`](docs/INTEGRATION_GUIDE.md) — Decoupled development and testing workflows.
- **Engineering Disciplines & Ownership:** [`docs/TEAM_RESPONSIBILITIES.md`](docs/TEAM_RESPONSIBILITIES.md) — Responsibility matrix.

---

## 10. Current Implementation Status

| Component | Status | Description |
|---|---|---|
| **Repository & Governance** | **Complete** | Cloned repository, Git safety policies, contribution workflows established. |
| **Interface Contracts** | **Complete** | Canonical `CONTRACT.md`, shared audio constants, 4-class taxonomy, Pydantic schemas. |
| **Developer Tooling** | **Complete** | `requirements.txt`, `backend/Dockerfile`, `docker-compose.yml`, test harnesses. |
| **Verification Suites** | **Complete** | `scripts/validate_contracts.py` (7/7 passed), `scripts/test_api.py` (6/6 passed). |
| **Backend & Pipeline Core** | *Pending* | FastAPI routes (`/health`, `/pipelines`, `/alerts`, `/tickets`), ring buffer, WebSocket streamer. |
| **ML Inference Engine** | *Pending* | 4-class CNN model weights, Butterworth DSP filtering, inference callable. |
| **Frontend GIS Dashboard** | *Pending* | React UI, Canvas waterfall spectrogram, Leaflet map, work-order modal. |
| **Demo Audio & Fixtures** | *Pending* | Real/synthetic WAV audio samples for all 4 classes, GeoJSON pipeline network. |
