# Backend & Infrastructure

The **Backend & Infrastructure** domain powers the SynthLeak real-time acoustic pipeline monitoring system. It provides high-throughput digital signal processing (DSP), asynchronous REST APIs, WebSocket streaming telemetry, relational SQLite persistence via SQLAlchemy, and Time Difference of Arrival (TDoA) cross-correlation localization.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Audio Engine / Sensors    |
                      +--------------+--------------+
                                     | Raw PCM 44.1 kHz
                                     v
                      +-----------------------------+
                      | Circular Ring Audio Buffer  |
                      |   (65,536 samples / 1.48s)  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  DSP Mel Spectrogram Engine |
                      |    (STFT -> 128 Mel Bins)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    ML Inference Adapter     |
                      | (4-Class Acoustic Classifier|
                      +--------------+--------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
+----------------------------------+   +-----------------------------------+
|      FastAPI REST Endpoints      |   |        WebSocket Streamer         |
|  /health, /pipelines, /alerts,   |   |            /ws/stream             |
|             /tickets             |   | (128-bin Mel frames @ 15-20 FPS)  |
+----------------+-----------------+   +-----------------+-----------------+
                 |                                       |
                 v                                       v
+--------------------------------------------------------------------------+
|                        SQLite Storage / SQLAlchemy                       |
|           (Pipelines, Sensors, Alerts, Work-Order Tickets)               |
+--------------------------------------------------------------------------+
```

---

## Directory Structure

```
backend/
├── __init__.py               # Package marker
├── main.py                   # FastAPI application entrypoint & lifespan hooks
├── config.py                 # Centralized configuration & environment loader
├── database.py               # SQLAlchemy engine, session maker, and DB dependencies
├── models.py                 # Relational ORM models (Pipeline, Sensor, Alert, Ticket)
├── seed.py                   # Database table initialization & canonical data seeding
├── audio_buffer.py           # Thread-safe circular audio buffer & Mel DSP processor
├── simulation.py             # Synthetic audio generation & 4-class scenario replayer
├── ml_adapter.py             # ML inference adapter conforming to InferenceOutput schema
├── localization.py           # Dual-sensor acoustic cross-correlation & TDoA localization
├── websocket_manager.py      # Multi-client WebSocket connection manager & broadcaster
├── services.py               # Alert evaluation, deduplication & ticket dispatch services
├── routes_pipelines.py       # REST route handlers for GET /pipelines
├── routes_alerts.py          # REST route handlers for GET /alerts
├── routes_tickets.py         # REST route handlers for POST /tickets
├── routes_ws.py              # WebSocket endpoint WS /ws/stream
├── test_backend.py           # Comprehensive unit & integration test suite
└── Dockerfile                # Container build specification for backend service
```

---

## API Endpoints

All schemas strictly implement [`CONTRACT.md`](../CONTRACT.md).

### REST APIs
- `GET /health` — System readiness and subsystem status (`database`, `audio_buffer`, `ml_inference`, `websocket_stream`).
- `GET /pipelines` — Query monitored pipeline segments with GeoJSON geometries and attached sensors. Supports `material` and `status` query filters.
- `GET /alerts` — Anomaly detection event log with `pipeline_id`, `severity`, and `acknowledged` query filters.
- `POST /tickets` — Dispatch a field maintenance work-order. Auto-generates canonical ticket ID (`TKT-YYYYMMDD-XXXX`), associates with the alert, and updates acknowledgment status.

### Real-Time Streaming
- `WS /ws/stream` — Continuous WebSocket broadcasting of 128-bin normalized Mel spectrogram frames (`SpectrogramFrameMessage`) at 15 FPS with instantaneous RMS sound levels (`dBFS`) and classification summaries. Supports client ping/pong keepalives (`HeartbeatMessage`).

---

## Local Development & Setup

### 1. Prerequisites
- Python 3.10+ (tested and verified on Python 3.13)
- Virtual environment (`.venv`)

### 2. Dependency Installation
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Launching the Backend Server
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Documentation (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Running Automated Tests

```bash
# 1. Run backend unit & integration tests:
python -m pytest backend/test_backend.py -v

# 2. Run canonical contract validation:
python scripts/validate_contracts.py

# 3. Run live API harness against running backend:
python scripts/test_api.py --url http://127.0.0.1:8000
```

---

## Production Deployment on Render

The SynthLeak backend is pre-configured for direct deployment on [Render](https://render.com) as a Web Service.

### Quick Deploy via Render Blueprint
A ready-to-use [`render.yaml`](../render.yaml) is provided in the repository root:
1. In the Render Dashboard, click **New +** -> **Blueprint**.
2. Connect the `SynthLeak` repository.
3. Render reads `render.yaml` and provisions the `synthleak-backend` web service with the exact configuration.

### Manual Web Service Configuration
If creating a Web Service manually in the Render dashboard:

| Setting | Value |
|---|---|
| **Name** | `synthleak-backend` |
| **Language / Runtime** | `Python 3` |
| **Region** | `Oregon (US West)` or preferred region |
| **Branch** | `main` |
| **Root Directory** | *(leave empty — repository root)* |
| **Build Command** | `pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |
| **Auto-Deploy** | `Yes` |

> **PyTorch CPU Build:** The build command installs the lightweight CPU-only wheel of PyTorch (~150MB instead of ~1GB CUDA wheel), preventing memory exhaustion and build timeouts on Render tiers.

### Recommended Environment Variables

| Variable | Recommended Value | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production error reporting & suppresses tracebacks |
| `LOG_LEVEL` | `info` | Server logging level |
| `PYTHONPATH` | `.` | Ensures Python locates root packages (`backend`, `shared`, `ml`) |
| `CORS_ORIGINS` | `http://localhost:5173,https://your-frontend.netlify.app,https://your-frontend.vercel.app` | Comma-separated list of permitted frontend origins |
| `CORS_ORIGIN_REGEX` | `https://.*(netlify\.app\|vercel\.app\|onrender\.com).*` | Regex allowing dynamic Netlify & Vercel deployment preview URLs |
| `DATABASE_PATH` | `/app/data/synthleak.db` (ephemeral) or `/var/data/synthleak.db` (with Persistent Disk) | SQLite database storage path |

### Database Persistence & Render Disks
- **Free Tier (Ephemeral Storage):** On Render's Free tier, the local SQLite database resides in `./data/synthleak.db`. When Render spins down or restarts an idle service, the database re-seeds automatically on startup via `setup_database()`.
- **Persistent Storage (Render Starter Tier):** For permanent ticket and alert retention across restarts:
  1. Add a **Persistent Disk** in Render (Name: `synthleak-data`, Mount Path: `/var/data`, Size: 1 GB).
  2. Set the environment variable: `DATABASE_PATH=/var/data/synthleak.db`.
  3. The backend automatically creates `/var/data` parent directories on startup if they do not exist.

### WebSocket Streaming on Render
- Render supports WebSockets natively on all plans with no extra configuration.
- The frontend connects to `wss://<your-render-service-name>.onrender.com/ws/stream`.
- SynthLeak's continuous 15 FPS frame stream and 5-second heartbeats prevent Render's 55-second proxy idle timeout from closing connections.

---

## Team Integration Interfaces

### Acoustic Signal Processing & ML
- Import audio constants from [`shared/constants.py`](../shared/constants.py).
- Deliver trained weights or callable model to [`backend/ml_adapter.py`](ml_adapter.py) implementing `InferenceOutput`.

### Audio Engine & Hardware Ingestion
- Pipe continuous 44.1 kHz PCM audio frames directly into `CircularAudioBuffer.write(samples)`.

### Frontend & GIS Development
- Connect WebSocket client to `/ws/stream` to receive `SpectrogramFrameMessage` arrays for the Canvas waterfall spectrogram.
- Query `/pipelines` to render Leaflet GeoJSON pipe geometries.
- Post ticket creation requests to `/tickets`.
