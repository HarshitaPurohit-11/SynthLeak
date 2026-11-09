# Frontend & GIS Dashboard

The frontend application provides an operator interface for real-time acoustic pipeline monitoring, live spectral waterfall visualization, interactive GIS mapping, and work-order dispatch.

---

## Responsibilities

- **Live Spectrogram Waterfall:** Renders continuous rolling Mel spectrogram frames received over WebSocket at 10–20 FPS using HTML5 Canvas / WebGL.
- **Interactive GIS Map:** Visualizes pipeline network segments, sensor locations, dynamic status indicators, and estimated leak positions using Leaflet.js.
- **Real-Time Telemetry:** Displays sound levels (dBFS), model classification confidence scores, and dominant acoustic frequencies (Hz).
- **Incident Management:** Shows real-time anomaly alerts with severity badges and provides a work-order dispatch modal to create maintenance tickets via `POST /tickets`.
- **Demo Controls:** Supports switching between live audio stream monitoring and canned scenario replays.

---

## Directory Layout

```
frontend/
├── public/                 # Static assets, icons, and GeoJSON fixtures
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Map/            # Leaflet map and pipeline layer renderers
│   │   ├── Spectrogram/    # HTML5 Canvas waterfall spectrogram
│   │   ├── Telemetry/      # Sound level gauges and frequency meters
│   │   ├── Alerts/         # Incident alert banner and list
│   │   └── WorkOrders/     # Ticket dispatch modal and forms
│   ├── hooks/              # Custom React hooks (useWebSocket, usePipelines)
│   ├── services/           # REST client and WebSocket communication
│   ├── types/              # TypeScript definitions matching CONTRACT.md
│   ├── App.tsx             # Root layout and state orchestration
│   └── main.tsx            # Application entry point
├── package.json            # Node dependencies and scripts
└── vite.config.ts          # Vite configuration and proxy rules
```

---

## Development & Testing

### Prerequisites
- Node.js 18+
- npm or pnpm

### Setup & Local Development
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/health`, `/pipelines`, `/alerts`, `/tickets` and `/ws` to the backend at
`http://localhost:8000` (override with `BACKEND_URL=http://host:8000 npm run dev`), so no CORS setup is needed.

**No backend yet?** Click **Demo replay** in the top bar (or open `http://localhost:5173/?mode=demo`). It plays a
looping, clearly labelled *simulated* scenario (traffic baseline, pinhole leak, burst, repair) and exercises the whole
flow: spectrogram, alerts, map, work-order dispatch.

### Running Tests / Build
```bash
npm run test         # unit tests (mel mapping, contract parsing, geometry, demo scenario, ticket form)
npm run typecheck
npm run build        # production bundle in dist/
```

### Docker
`frontend/Dockerfile` builds the bundle and serves it with nginx, reverse-proxying the API and WebSocket to the
`backend` service. Add this to `docker-compose.yml` (root file, owned by Backend & Infrastructure):
```yaml
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
```

## Behaviour notes
- **Live backend** mode consumes `ws://<host>/ws/stream` and REST `GET /pipelines`, `GET /alerts` (polled every 5 s and
  right after an alert frame), `POST /tickets`. Unknown or malformed WebSocket messages are ignored; the socket
  reconnects with backoff and the UI shows the connection state. After 3 failed attempts it offers Demo replay.
- **Demo replay** never touches the network. Every simulated frame, alert and ticket is labelled "Simulated"
  (`SIM-ALT-*`, `SIM-WO-*`), per the metric-integrity rule in `CONTRACT.md` section 8.
- **Adaptive Noise Suppression toggle** is *display-side only*: the waterfall learns the background from frames the
  model labelled NORMAL_FLOW / AMBIENT_URBAN and subtracts it from what you see. It does not change the backend's
  model input (the contract has no control message for that).
- Estimated leak position comes from `estimated_chainage_meters` in the alert record, interpolated along the pipeline
  geometry. Nothing is shown if the backend does not provide it.
- The map uses OpenStreetMap tiles; offline, pipelines still draw on a plain background.

---

## Interface Contracts
- **WebSocket Telemetry:** Consumes messages conforming to [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream).
- **Pipelines Endpoint:** Consumes [`CONTRACT.md`](../CONTRACT.md#61-get-pipelines).
- **Alerts Endpoint:** Consumes [`CONTRACT.md`](../CONTRACT.md#62-get-alerts).
- **Tickets Endpoint:** Submits payloads conforming to [`CONTRACT.md`](../CONTRACT.md#63-post-tickets).

