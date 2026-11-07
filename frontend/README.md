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
npm run dev
```

The application will run on `http://localhost:3000` or `http://localhost:5173` and connect to the backend API at `http://localhost:8000`.

### Running Tests
```bash
npm run test
```

---

## Interface Contracts
- **WebSocket Telemetry:** Consumes messages conforming to [`CONTRACT.md`](../CONTRACT.md#5-real-time-dashboard-stream).
- **Pipelines Endpoint:** Consumes [`CONTRACT.md`](../CONTRACT.md#61-get-pipelines).
- **Alerts Endpoint:** Consumes [`CONTRACT.md`](../CONTRACT.md#62-get-alerts).
- **Tickets Endpoint:** Submits payloads conforming to [`CONTRACT.md`](../CONTRACT.md#63-post-tickets).

