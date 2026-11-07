# SynthLeak API & Protocol Specification

**Status:** Canonical Reference (Derived from `CONTRACT.md`)  
**Base URL:** `http://localhost:8000`  
**WebSocket URL:** `ws://localhost:8000/ws/stream`  
**Version:** 1.0.0

---

## 1. REST Endpoints

### 1.1 `GET /health`
Checks server health, database connectivity, and ML model readiness.

- **Method:** `GET`
- **Path:** `/health`
- **Authentication:** None
- **Success Response:** `200 OK`
```json
{
  "status": "HEALTHY",
  "version": "1.0.0",
  "timestamp": "2026-11-07T10:55:00.000Z",
  "components": {
    "database": "CONNECTED",
    "ml_engine": "READY",
    "audio_stream": "ACTIVE"
  }
}
```

---

### 1.2 `GET /pipelines`
Retrieves monitored pipeline network segments, structural metadata, and spatial coordinates.

- **Method:** `GET`
- **Path:** `/pipelines`
- **Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `status` | `string` | No | `null` | Filter by status (`NORMAL`, `WARNING`, `CRITICAL`, `OFFLINE`) |
| `limit` | `integer` | No | `50` | Maximum number of pipelines returned (max: 200) |
| `offset` | `integer` | No | `0` | Number of items to skip for pagination |

- **Success Response:** `200 OK`
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

- **Error Responses:**
  - `500 Internal Server Error` (Database query failure).

---

### 1.3 `GET /alerts`
Retrieves acoustic anomaly logs, leak alerts, and classification details.

- **Method:** `GET`
- **Path:** `/alerts`
- **Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `pipeline_id` | `string` | No | `null` | Filter alerts for a specific pipeline |
| `severity` | `string` | No | `null` | Filter by severity (`INFO`, `WARNING`, `CRITICAL`) |
| `is_acknowledged` | `boolean` | No | `null` | Filter by acknowledgment status |
| `limit` | `integer` | No | `50` | Maximum items to return (max: 200) |
| `offset` | `integer` | No | `0` | Offset for pagination |

- **Success Response:** `200 OK`
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

---

### 1.4 `POST /tickets`
Dispatches a field repair work order associated with an acoustic alert.

- **Method:** `POST`
- **Path:** `/tickets`
- **Headers:** `Content-Type: application/json`
- **Request Body Fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `alert_id` | `string` | Yes | Existing alert identifier |
| `pipeline_id` | `string` | Yes | Target pipeline identifier |
| `priority` | `string` | Yes | Enum: `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"` |
| `assigned_crew` | `string` | No | Crew name or field unit ID |
| `description` | `string` | Yes | Detailed description of the maintenance work |
| `location_estimate` | `object` | No | Estimated geographic location and chainage |

- **Request Example:**
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

- **Success Response:** `201 Created`
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

---

## 2. Standard Error Format

All error responses return a structured JSON body adhering to:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'priority' must be one of LOW, MEDIUM, HIGH, CRITICAL",
    "details": [
      {
        "field": "priority",
        "issue": "Invalid value provided: 'URGENT'"
      }
    ],
    "timestamp": "2026-11-07T10:56:15.000Z"
  }
}
```

### Common HTTP Status Codes
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Malformed JSON or request syntax error.
- `404 Not Found`: Alert or Pipeline ID not found.
- `422 Unprocessable Entity`: Schema constraint or validation violation.
- `500 Internal Server Error`: Server-side unhandled exception.

---

## 3. Real-Time WebSocket Protocol

- **Endpoint:** `ws://<host>:<port>/ws/stream`
- **Protocol:** Text WebSocket messages containing JSON.
- **Broadcast Frequency:** 10 to 20 frames per second.

### Spectrogram Frame Payload
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

### Heartbeat Frame Payload
```json
{
  "message_type": "heartbeat",
  "timestamp": "2026-11-07T10:55:05.000Z",
  "status": "OK",
  "active_clients": 1
}
```

