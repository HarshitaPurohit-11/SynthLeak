# SynthLeak

**Real-Time Acoustic Pipeline Leak Detection and Localization Platform**

---

## 1. Quick Start: Run Locally on Windows (One-Click)

The simplest way to run SynthLeak locally without Docker is using the dedicated Windows startup scripts.

### Prerequisites
- **Windows 10 / 11**
- **Python 3.10+** (Python 3.13 supported; installed with `.venv` in repository)
- **Node.js 18+** (Node 22 / npm included on system PATH)

### Starting the Complete System
1. Open the project root folder: `C:\Users\Admin\Desktop\SynthLeak`
2. **Double-click [`start-dev.bat`](start-dev.bat)** (or execute `.\start-dev.bat` in Command Prompt / PowerShell).

This one-click launcher automatically:
- Activates your existing Python `.venv`.
- Verifies and installs missing frontend `node_modules` (first-time only).
- Launches the **FastAPI Backend & ML DSP Streamer** on port `8000` in its own window.
- Launches the **React + Leaflet GIS Dashboard** on port `5173` in its own window.
- Automatically opens your default web browser to [http://localhost:5173](http://localhost:5173).
- Displays live diagnostic logs in both command windows.

### Stopping the System
- **Double-click [`stop-dev.bat`](stop-dev.bat)** (or close both command prompt windows).  
  This cleanly releases ports `8000` and `5173`.

---

## 2. Essential URLs & Endpoints

| Service / Interface | Local URL | Description |
|---|---|---|
| **Operator Dashboard (UI)** | [http://localhost:5173](http://localhost:5173) | React GIS Leaflet map, waterfall spectrogram, alert stream, work orders |
| **Backend REST API** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Core FastAPI server |
| **Interactive API Docs (Swagger)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | OpenAPI interactive endpoint exploration & testing |
| **Alternative API Docs (ReDoc)** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Clean schema & payload documentation |
| **System Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Subsystem health (`database`, `ml_inference`, `audio_buffer`) |
| **Real-Time Audio Stream** | `ws://127.0.0.1:8000/ws/stream` | 128-bin Mel spectrogram frames & classification scores @ 15 FPS |

---

## 3. First-Time Manual Setup (Alternative to start-dev.bat)

If you prefer starting backend and frontend in separate manual terminals:

### Step 1: Backend Setup
```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate

# 2. Start FastAPI server with live reload
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 2: Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (one-time)
npm install

# 3. Start Vite development server
npm run dev
```

---

## 4. System Architecture & Capabilities

```
+-----------------------------------------------------------------------------------+
|                            ACOUSTIC INGESTION PIPELINE                            |
|                                                                                   |
|  [Microphone / Sensor]  or  [Scenario Replayer]  (44.1 kHz PCM Audio)             |
|                                |                                                  |
|                                v                                                  |
|  [Circular Ring Buffer] (65,536 float32 samples / 1.48s clip)                     |
|                                |                                                  |
|                                v                                                  |
|  [DSP & Mel Filtering] (4th-order Butterworth + 128-bin Mel Spectrogram)          |
|                                |                                                  |
|                                v                                                  |
|  [4-Class CNN Classifier] (leak_cnn.pt -> NORMAL, AMBIENT, PINHOLE, CAVITATION)  |
+--------------------------------+--------------------------------------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
        v                                                 v
+-------------------------------+       +-------------------------------------------+
|    FastAPI REST Endpoints     |       |         WebSocket Streamer (/ws)          |
| /health, /pipelines, /alerts, |       | (128-bin normalized Mel frames @ 15 FPS,  |
|            /tickets           |       |      dBFS sound level, classifications)   |
+---------------+---------------+       +---------------------+---------------------+
                |                                             |
                v                                             v
+-----------------------------------------------------------------------------------+
|                        OPERATOR DASHBOARD (React + Leaflet)                       |
|                                                                                   |
| - Canvas Rolling Waterfall Spectrogram (Color-mapped 128 Mel frequency bins)      |
| - Interactive Leaflet Map with GeoJSON pipeline geometries & sensor markers       |
| - TDoA Cross-Correlation Acoustic Localization along pipe chainage                |
| - Real-time Anomaly Alert Log & Work-Order Ticket Dispatch Modal                  |
+-----------------------------------------------------------------------------------+
```

---

## 5. Audio Engine: Real Hardware Capture vs. Simulation

SynthLeak dynamically detects acoustic hardware input:

1. **Physical Hardware Capture (Microphone / Sensor):**
   - [`audio-engine/capture.py`](audio-engine/capture.py) queries system audio input devices via `sounddevice`.
   - When a microphone is connected, it acquires live acoustic emissions directly into the ring buffer.
   - Streamed frames carry `"is_simulated": false`.
2. **Synthetic Simulation Mode (Automated Fallback):**
   - If no physical sensor or microphone is detected, the audio engine automatically engages [`backend/simulation.py`](backend/simulation.py).
   - Replays reproducible 4-class pipeline acoustic signatures (`NORMAL_FLOW`, `AMBIENT_URBAN`, `PINHOLE_LEAK`, `CAVITATION_BURST`).
   - Streamed frames carry `"is_simulated": true` and the dashboard displays a **`Simulated`** badge in compliance with metric integrity guidelines.

---

## 6. Automated Testing & Verification

SynthLeak includes an automated verification suite across all layers:

```bash
# 1. Run Backend Unit & Integration Tests:
.venv\Scripts\python -m pytest backend/test_backend.py -v

# 2. Run Machine Learning Classifier Tests:
.venv\Scripts\python -m pytest ml/tests/ -v

# 3. Run Audio Engine DSP Tests:
.venv\Scripts\python -m pytest audio-engine/tests/ -v

# 4. Run Shared Contract & Schema Verification:
.venv\Scripts\python scripts/validate_contracts.py

# 5. Run API Test Harness against Live Server:
.venv\Scripts\python scripts/test_api.py --url http://127.0.0.1:8000

# 6. Run Frontend TypeScript Verification:
cd frontend && npm run typecheck
```

---

## 7. Optional Container Deployment (Docker)

Docker is completely optional. If you wish to build or deploy the project in containers:

```bash
# Build and start both backend and frontend via Docker Compose:
docker compose up --build -d

# View logs:
docker compose logs -f

# Shut down containers:
docker compose down
```

---

## 8. Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| **Port 8000 already in use** | An earlier instance of Uvicorn or another service is listening on port 8000. | Run [`stop-dev.bat`](stop-dev.bat) to terminate stale processes. |
| **Port 5173 already in use** | An earlier Vite development server is running. | Run [`stop-dev.bat`](stop-dev.bat) or let Vite choose port 5174. |
| **`python.exe` not found** | Virtual environment `.venv` is missing or moved. | Run `python -m venv .venv` and install `requirements.txt`. |
| **`npm` command not recognized** | Node.js is not on your Windows user PATH. | Install Node.js v18+ from [nodejs.org](https://nodejs.org) or ensure `C:\nvm4w\nodejs` is in your environment PATH. |
| **Database uninitialized** | `data/synthleak.db` not found. | The database initializes automatically upon backend launch via `backend/seed.py`. You do not need to seed manually. |

---

## 9. Documentation Directory

- **Canonical Interface Contract:** [`CONTRACT.md`](CONTRACT.md) — Authoritative schemas, endpoints, and taxonomy.
- **Project Guidelines:** [`PROJECT_GUIDELINES.md`](PROJECT_GUIDELINES.md) — Architectural rules and domain ownership.
- **Contribution Workflow:** [`CONTRIBUTING.md`](CONTRIBUTING.md) — Change protocols and Git standards.
- **System Architecture:** [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) — DSP filters, TDoA cross-correlation math, and ML topology.
- **API Specification:** [`docs/API_SPECIFICATION.md`](docs/API_SPECIFICATION.md) — Comprehensive REST & WebSocket specs.
- **Backend Guide:** [`backend/README.md`](backend/README.md) — Deep dive into FastAPI internals and database models.
- **Frontend Guide:** [`frontend/README.md`](frontend/README.md) — React dashboard components and Leaflet GIS integration.
- **ML Guide:** [`ml/README.md`](ml/README.md) — CNN model architecture, training, and evaluation reports.
