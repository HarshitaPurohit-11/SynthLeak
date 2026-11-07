# Backend & Infrastructure

The backend service powers SynthLeak's real-time ingestion, ML inference execution, streaming distribution, spatial data persistence, and work-order management.

---

## Responsibilities

- **FastAPI Core:** Exposes asynchronous REST endpoints (`GET /health`, `GET /pipelines`, `GET /alerts`, `POST /tickets`).
- **WebSocket Streaming:** Distributes real-time Mel spectrogram frames, instantaneous classification scores, and alert notifications to connected dashboards via `/ws/stream` at 10–20 FPS.
- **Audio Capture & Buffering:** Captures live audio streams or scenario audio into a thread-safe circular ring buffer (`CLIP_SAMPLES = 65536`).
- **Inference Integration:** Asynchronously offloads ML classification calls to Python worker threads (`asyncio.to_thread`) to ensure non-blocking WebSocket delivery.
- **Data Persistence:** Manages SQLite storage (`synthleak.db`) for pipeline infrastructure, alert logs, and work-order tickets.
- **Cross-Correlation Localization:** Estimates leak locations along pipe segments using Time Difference of Arrival (TDoA) cross-correlation.
- **Deployment:** Provides containerized execution via `Dockerfile` and `docker-compose.yml`.

---

## Directory Layout

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Runtime configuration and environment settings
├── routes/                 # REST and WebSocket route handlers
│   ├── health.py           # Health check endpoint
│   ├── pipelines.py        # Pipeline querying and GeoJSON delivery
│   ├── alerts.py           # Anomaly log querying
│   ├── tickets.py          # Work-order dispatch
│   └── websocket.py        # Real-time WebSocket stream broadcaster
├── services/               # Business logic and coordination
│   ├── audio_stream.py     # Buffer consumer and stream dispatcher
│   ├── alert_engine.py     # Thresholding and incident creation
│   └── localization.py     # TDoA acoustic cross-correlation
├── db/                     # SQLite models, migrations, and repository layer
│   ├── connection.py       # Thread-safe SQLite connection pool
│   └── repositories.py     # Data access queries
└── tests/                  # Unit and integration test suite
```

---

## Development & Testing

### Prerequisites
- Python 3.10+
- Dependencies listed in the root `requirements.txt`

### Running the Server Locally
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
pytest backend/tests/ -v
```

---

## Interface Contracts
- **ML Inference:** Implements the callable defined in [`CONTRACT.md`](../CONTRACT.md#4-ml-inference-interface).
- **Dashboard Stream:** Broadcasts frames conforming to [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream).
- **REST Endpoints:** Conforms to [`CONTRACT.md`](../CONTRACT.md#6-rest-api-interface).
- **Database Schema:** Matches [`CONTRACT.md`](../CONTRACT.md#7-database-schema--entity-definitions).

