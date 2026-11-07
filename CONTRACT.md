# SynthLeak Shared Communication Contract & Interface Specification

**Version:** 1.0.0  
**Status:** CANONICAL INTERFACE SPECIFICATION  
**Last Updated:** 2026-11-07  
**Applies to:** Acoustic Signal Processing & ML, Frontend & GIS Development, Backend & Infrastructure, Demo Production & Documentation

---

## 1. Governance & Authority

This document (`CONTRACT.md`) is the canonical contract governing all data interchange, interface boundaries, shared constants, and system protocols across the SynthLeak platform.

- **Immutable without Consensus:** No contributor or automated assistant may unilaterally alter any field, type, constant, or endpoint defined herein.
- **Change Procedure:** Any modification must follow the formal [Contract Change Protocol](#9-contract-change-management-protocol).
- **Precedence:** In case of conflict between code comments, legacy notes, or individual module documentation, this document takes precedence.

---

## 2. Shared Audio Constants & Configuration

All audio capture, DSP transformations, spectrogram conversions, and neural network inference must adhere to the following shared constants:

| Parameter | Constant Name | Value | Unit / Description |
|---|---|---|---|
| Sampling Rate | `SAMPLE_RATE` | `44100` | Hz (Standard audio sampling rate) |
| FFT Window Size | `N_FFT` | `1024` | Samples (~23.22 ms window) |
| Hop Length | `HOP_LENGTH` | `512` | Samples (50% overlap, ~11.61 ms stride) |
| Mel Filter Bins | `N_MELS` | `128` | Number of Mel frequency bands |
| Window Function | `WINDOW_FN` | `"hann"` | Hann window for STFT computation |
| Spectrogram Shape | `SPECTROGRAM_SHAPE` | `(128, 128)` | Frequency bins × Time frames |
| Audio Clip Samples | `CLIP_SAMPLES` | `65536` | $128 \times 512 = 65536$ samples (~1.486 sec) |
| Frequency Cutoff Low | `FILTER_LOW_CUT_HZ` | `100.0` | Default high-pass / bandpass cutoff in Hz |
| Frequency Cutoff High | `FILTER_HIGH_CUT_HZ` | `10000.0` | Default low-pass / bandpass cutoff in Hz |

### Technical Decision on Bandpass Filter Mismatch
- **Architecture Specification:** Defines a bandpass range of **100 Hz to 10 kHz**.
- **Initial DSP Code:** Used **500 Hz to 9 kHz**.
- **Contract Decision:** The Acoustic Signal Processing & ML team owns internal DSP filtering. The backend processes inference output agnostic of internal filter cutoffs. The system default standard for filtering is agreed as **100 Hz to 10 kHz** with **500 Hz to 9 kHz** accepted as an active noise-suppression filter preset tuned for urban mechanical vibration rejection.

---

## 3. Acoustic Classification Labels & Mappings

The neural classifier and backend alert engines must strictly use the following 4-class taxonomy:

| Class ID (`class_id`) | Label String (`class_label`) | Description | Default Alert Severity | Triggers Alarm? |
|---|---|---|---|---|
| `0` | `NORMAL_FLOW` | Normal laminar/turbulent fluid flow within pipe | `NONE` | No (`false`) |
| `1` | `AMBIENT_URBAN` | Environmental acoustic interference (traffic, HVAC, footsteps) | `INFO` | No (`false`) |
| `2` | `PINHOLE_LEAK` | High-frequency acoustic hiss/jet from small pipe orifice | `WARNING` | Yes (`true`) |
| `3` | `CAVITATION_BURST` | Sudden transient burst, hydraulic hammer, vapor pocket collapse | `CRITICAL` | Yes (`true`) |

---

## 4. ML Inference Interface

### 4.1 Expected Python Interface
The Acoustic Signal Processing & ML module exposes a prediction callable that the Backend invokes within an asynchronous worker or thread pool:

```python
from typing import Dict, Any, Union
import numpy as np

class LeakClassifierInterface:
    def predict(self, audio_data: np.ndarray, sample_rate: int = 44100) -> Dict[str, Any]:
        """
        Executes DSP preprocessing, Mel spectrogram generation, and 4-class CNN inference.
        
        Parameters:
            audio_data (np.ndarray): 1D float32 numpy array with shape (65536,) or (N,)
            sample_rate (int): Sampling rate, default 44100 Hz
            
        Returns:
            Dict[str, Any] conforming to the Inference Output Schema.
            
        Raises:
            ValueError: If audio_data is empty, non-1D, or contains non-finite values (NaN/Inf).
            RuntimeError: If model weights are uninitialized or inference fails.
        """
        ...
```

### 4.2 Inference Output Data Schema

| Field | Type | Permitted Values | Validation Rules | Description |
|---|---|---|---|---|
| `class_id` | `integer` | `0`, `1`, `2`, `3` | Must match one of 4 defined IDs | Numeric category code |
| `class_label` | `string` | `"NORMAL_FLOW"`, `"AMBIENT_URBAN"`, `"PINHOLE_LEAK"`, `"CAVITATION_BURST"` | Must match `class_id` precisely | Human-readable classification |
| `confidence` | `float` | `0.0` to `1.0` | Softmax probability, rounded to 4 decimals | Confidence score |
| `peak_frequency_hz` | `float` | $\ge 0.0$ | Spectral frequency with maximum energy | Dominant frequency in Hz |
| `timestamp` | `string` | ISO 8601 UTC string (`YYYY-MM-DDTHH:MM:SS.sssZ`) | Valid UTC datetime | Timestamp of prediction |

### 4.3 JSON Example: Inference Output
```json
{
  "class_id": 2,
  "class_label": "PINHOLE_LEAK",
  "confidence": 0.9425,
  "peak_frequency_hz": 4250.0,
  "timestamp": "2026-11-07T10:55:00.120Z"
}
```

### 4.4 Error Handling & Fallbacks
- If input audio contains invalid floating-point values (`NaN`, `Inf`), the function raises a `ValueError("Invalid audio data: NaN or Inf detected")`.
- If input audio length is less than `N_FFT`, it must be zero-padded or raise `ValueError("Audio buffer too short for FFT window")`.
- The backend wraps this invocation in a `try/except` block and falls back to:
```json
{
  "class_id": 1,
  "class_label": "AMBIENT_URBAN",
  "confidence": 0.0,
  "peak_frequency_hz": 0.0,
  "timestamp": "2026-11-07T10:55:00.120Z",
  "error": "Inference computation failed: [error details]"
}
```

---

## 5. Real-Time Dashboard Stream

WebSocket URL: `ws://<host>:<port>/ws/stream`

### 5.1 Message Types
The WebSocket connection broadcasts continuous real-time frames and system events:
1. `spectrogram_frame`: Real-time audio analysis, 128 Mel energy values, sound pressure, classification, and alert state.
2. `heartbeat`: Periodic keepalive frame (every 5 seconds).

### 5.2 Spectrogram Frame Message Structure

| Field | Type | Required | Description |
|---|---|---|---|
| `message_type` | `string` | Yes | Always `"spectrogram_frame"` |
| `timestamp` | `string` | Yes | ISO 8601 UTC timestamp |
| `pipeline_id` | `string` | Yes | Monitored pipeline identifier (e.g. `"PIPE-001"`) |
| `sensor_id` | `string` | Yes | Sensor unit identifier (e.g. `"SENSOR-A1"`) |
| `spectrogram_frame` | `array[float]` | Yes | Exactly 128 normalized float values (0.0 to 1.0) representing current Mel bin energies |
| `classification` | `object` | Yes | Embedded inference results |
| `classification.class_id` | `integer` | Yes | 0, 1, 2, or 3 |
| `classification.class_label` | `string` | Yes | Label string |
| `classification.confidence` | `float` | Yes | Softmax confidence (0.0 to 1.0) |
| `classification.dominant_frequency_hz` | `float` | Yes | Dominant peak frequency in Hz |
| `sound_level_db` | `float` | Yes | RMS sound level in dBFS (-90.0 to 0.0 dB) |
| `alert` | `object` | Yes | Alert evaluation object |
| `alert.is_alert` | `boolean` | Yes | `true` if leak detected (class 2 or 3) |
| `alert.severity` | `string` | Yes | `"NONE"`, `"INFO"`, `"WARNING"`, `"CRITICAL"` |
| `alert.message` | `string` | Yes | Human-readable alert summary |

### 5.3 JSON Example: WebSocket Message
```json
{
  "message_type": "spectrogram_frame",
  "timestamp": "2026-11-07T10:55:00.120Z",
  "pipeline_id": "PIPE-001",
  "sensor_id": "SENSOR-A1",
  "spectrogram_frame": [
    0.05, 0.08, 0.12, 0.15, 0.22, 0.31, 0.45, 0.62,
    0.85, 0.94, 0.88, 0.72, 0.55, 0.38, 0.25, 0.18,
    0.12, 0.09, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03,
    0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01,
    0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01
  ],
  "classification": {
    "class_id": 2,
    "class_label": "PINHOLE_LEAK",
    "confidence": 0.9425,
    "dominant_frequency_hz": 4250.0
  },
  "sound_level_db": -18.4,
  "alert": {
    "is_alert": true,
    "severity": "WARNING",
    "message": "Acoustic anomaly: High-frequency pinhole leak signature on PIPE-001"
  }
}
```

---

## 6. REST API Interface

All REST endpoints accept and return `application/json`. Timestamps are formatted as ISO 8601 strings.

### 6.1 `GET /pipelines`
Retrieves pipeline network segments, operating state, and spatial geometry.

- **HTTP Method:** `GET`
- **URL:** `/pipelines`
- **Query Parameters:**
  - `status` (*optional*, string): Filter by status (`"NORMAL"`, `"WARNING"`, `"CRITICAL"`).
  - `limit` (*optional*, integer, default: `50`, max: `200`): Pagination limit.
  - `offset` (*optional*, integer, default: `0`): Pagination offset.
- **Success Status Code:** `200 OK`
- **Response Body:**
```json
{
  "total": 1,
  "items": [
    {
      "pipeline_id": "PIPE-001",
      "name": "Main Distribution Trunk A",
      "material": "Ductile Iron",
      "diameter_mm": 300.0,
      "length_meters": 1250.0,
      "status": "WARNING",
      "sensors": [
        {
          "sensor_id": "SENSOR-A1",
          "chainage_meters": 0.0,
          "latitude": 28.6139,
          "longitude": 77.2090
        },
        {
          "sensor_id": "SENSOR-A2",
          "chainage_meters": 1250.0,
          "latitude": 28.6210,
          "longitude": 77.2185
        }
      ],
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [77.2090, 28.6139],
          [77.2140, 28.6175],
          [77.2185, 28.6210]
        ]
      },
      "created_at": "2026-11-01T00:00:00.000Z",
      "updated_at": "2026-11-07T10:55:00.000Z"
    }
  ]
}
```

### 6.2 `GET /alerts`
Retrieves logged acoustic anomalies, leak alerts, and historical detections.

- **HTTP Method:** `GET`
- **URL:** `/alerts`
- **Query Parameters:**
  - `pipeline_id` (*optional*, string): Filter by pipeline ID.
  - `severity` (*optional*, string): Filter by severity (`"INFO"`, `"WARNING"`, `"CRITICAL"`).
  - `is_acknowledged` (*optional*, boolean): Filter by acknowledgment state.
  - `limit` (*optional*, integer, default: `50`, max: `200`): Maximum records to return.
  - `offset` (*optional*, integer, default: `0`): Pagination offset.
- **Success Status Code:** `200 OK`
- **Response Body:**
```json
{
  "total": 1,
  "items": [
    {
      "alert_id": "ALT-2026-0001",
      "pipeline_id": "PIPE-001",
      "sensor_id": "SENSOR-A1",
      "timestamp": "2026-11-07T10:55:00.120Z",
      "class_id": 2,
      "class_label": "PINHOLE_LEAK",
      "confidence": 0.9425,
      "dominant_frequency_hz": 4250.0,
      "sound_level_db": -18.4,
      "severity": "WARNING",
      "estimated_chainage_meters": 412.5,
      "is_acknowledged": false,
      "ticket_id": null
    }
  ]
}
```

### 6.3 `POST /tickets`
Dispatches a field maintenance work-order ticket linked to an acoustic alert.

- **HTTP Method:** `POST`
- **URL:** `/tickets`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "alert_id": "ALT-2026-0001",
  "pipeline_id": "PIPE-001",
  "priority": "HIGH",
  "assigned_crew": "Field Repair Unit Alpha",
  "description": "Acoustic detection indicated pinhole leak near chainage 412m. Clamp inspection required.",
  "location_estimate": {
    "latitude": 28.6162,
    "longitude": 77.2121,
    "chainage_meters": 412.5
  }
}
```
- **Validation Rules for Request:**
  - `alert_id`: Required string matching an existing alert.
  - `pipeline_id`: Required string matching an existing pipeline.
  - `priority`: Required enum (`"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"`).
  - `assigned_crew`: Optional string (maximum 100 characters).
  - `description`: Required non-empty string (maximum 500 characters).
  - `location_estimate`: Optional object containing `latitude` (-90 to 90), `longitude` (-180 to 180), and `chainage_meters` ($\ge 0$).
- **Success Status Code:** `201 Created`
- **Response Body:**
```json
{
  "ticket_id": "WO-2026-0001",
  "alert_id": "ALT-2026-0001",
  "pipeline_id": "PIPE-001",
  "priority": "HIGH",
  "status": "OPEN",
  "assigned_crew": "Field Repair Unit Alpha",
  "description": "Acoustic detection indicated pinhole leak near chainage 412m. Clamp inspection required.",
  "location_estimate": {
    "latitude": 28.6162,
    "longitude": 77.2121,
    "chainage_meters": 412.5
  },
  "created_at": "2026-11-07T10:56:15.000Z",
  "updated_at": "2026-11-07T10:56:15.000Z"
}
```

### 6.4 Standard Error Response Format
All error responses from any REST endpoint must conform strictly to the following schema:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Alert with ID 'ALT-9999-9999' was not found.",
    "details": [
      {
        "field": "alert_id",
        "issue": "No matching alert found in SQLite store."
      }
    ],
    "timestamp": "2026-11-07T10:56:15.000Z"
  }
}
```

Standard Error Codes:
- `BAD_REQUEST` (400) - Malformed JSON or request syntax error.
- `VALIDATION_ERROR` (422) - Field constraint or enum violation.
- `RESOURCE_NOT_FOUND` (404) - Pipeline or Alert record does not exist.
- `CONFLICT` (409) - Ticket already exists for the specified alert.
- `INTERNAL_SERVER_ERROR` (500) - Unhandled server exception.

---

## 7. SQLite Database Schema & Entity Contract

SQLite file: `synthleak.db` (managed by Backend & Infrastructure).

### Entity-Relationship Overview
```
+-------------------+        1:N        +-------------------+        1:1        +-------------------+
|     pipelines     | ----------------> |      alerts       | ----------------> | work_order_tickets|
+-------------------+                   +-------------------+                   +-------------------+
| id (PK)           |                   | id (PK)           |                   | id (PK)           |
| name              |                   | pipeline_id (FK)  |                   | alert_id (FK)     |
| material          |                   | sensor_id         |                   | pipeline_id (FK)  |
| diameter_mm       |                   | timestamp         |                   | priority          |
| length_meters     |                   | class_id          |                   | status            |
| status            |                   | class_label       |                   | assigned_crew     |
| coordinates_json  |                   | confidence        |                   | description       |
| created_at        |                   | dominant_freq_hz  |                   | est_lat, est_lon  |
| updated_at        |                   | severity          |                   | est_chainage_m    |
|                   |                   | is_acknowledged   |                   | created_at        |
|                   |                   | ticket_id (FK)    |                   | updated_at        |
+-------------------+                   +-------------------+                   +-------------------+
```

### DDL Specification
```sql
CREATE TABLE IF NOT EXISTS pipelines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    material TEXT NOT NULL,
    diameter_mm REAL NOT NULL,
    length_meters REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('NORMAL', 'WARNING', 'CRITICAL', 'OFFLINE')),
    coordinates_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    sensor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    class_id INTEGER NOT NULL CHECK(class_id IN (0, 1, 2, 3)),
    class_label TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    dominant_frequency_hz REAL NOT NULL,
    sound_level_db REAL NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('NONE', 'INFO', 'WARNING', 'CRITICAL')),
    estimated_chainage_meters REAL,
    is_acknowledged INTEGER NOT NULL DEFAULT 0 CHECK(is_acknowledged IN (0, 1)),
    ticket_id TEXT REFERENCES work_order_tickets(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS work_order_tickets (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    priority TEXT NOT NULL CHECK(priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status TEXT NOT NULL CHECK(status IN ('OPEN', 'DISPATCHED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    assigned_crew TEXT,
    description TEXT NOT NULL,
    estimated_latitude REAL,
    estimated_longitude REAL,
    estimated_chainage_meters REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_pipeline_id ON alerts(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_tickets_alert_id ON work_order_tickets(alert_id);
```

---

## 8. Technical Consistency Rules & Decisions

1. **Noise Terminology Standard:**
   - Always use **"Adaptive Noise Suppression"** (ANS).
   - Do **NOT** use "Active Noise Cancellation" (ANC), which refers to acoustic phase-cancelling hardware speakers. SynthLeak performs digital spectral subtraction and adaptive filtering.
2. **Hard-Coded Demo Claims Prohibition:**
   - Any static claim such as `"98.4% accuracy"` or `"0.8 mm pinhole orifice diameter"` must **never** be hard-coded into production payloads or presented as actual real-time measurements unless computed by an empirical model.
   - For demo simulation scenarios, synthetic payloads must clearly flag `"is_simulated": true` or be explicitly documented as simulation fixtures.
3. **Real-Time Integration Boundaries:**
   - **Audio Ingestion:** Handled by Backend & Infrastructure (`audio-engine/capture.py`). Captures chunks into a thread-safe ring buffer.
   - **DSP/Inference:** Backend pulls 65,536 samples from the ring buffer and executes inference in a background thread (`asyncio.to_thread`).
   - **WebSocket Stream Rate:** Spectrogram frames are broadcast at **10 to 20 frames per second** (downsampled from 86.1 fps raw STFT frames) to ensure smooth Leaflet/Canvas visualization on the frontend without saturating the browser event loop.

---

## 9. Contract Change Protocol

If an implementation requires modifying any schema, constant, or endpoint in this contract, the following protocol is mandatory:

1. **Initiate Change Proposal:** Document the proposed change with justification.
2. **Impact Assessment:** Identify every affected component (e.g. changing inference output affects both ML and Backend; changing WebSocket frames affects both Backend and Frontend).
3. **Backward Compatibility Check:** Determine whether the change breaks existing parsers or frontend widgets.
4. **Team Consensus:** All affected discipline leads review and sign off.
5. **Update Canonical Artifacts:**
   - Update `CONTRACT.md`.
   - Update `shared/constants.py` and `shared/schemas.py`.
   - Update all JSON examples in `shared/examples/`.
   - Run verification tests (`python scripts/validate_contracts.py`).
6. **Implementation:** Only after artifacts are updated and validated may developers update their local module code.

