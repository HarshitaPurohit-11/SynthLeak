# SynthLeak Data Formats & Serialization Reference

## 1. Acoustic & Spectrogram Data Formats

### 1.1 Raw PCM Audio Buffer
- **Type:** 1-dimensional IEEE 754 float32 NumPy array (`np.ndarray`).
- **Shape:** `(65536,)` corresponding to $128 \times 512$ audio samples (~1.486 seconds at 44,100 Hz).
- **Amplitude Range:** Normalized between `[-1.0, 1.0]`. Values exceeding this range must be clipped prior to DSP filtering.
- **Byte Order:** Little-endian (`<f4`).

### 1.2 STFT Log-Mel Spectrogram Matrix
- **Type:** 2-dimensional float32 tensor (`np.ndarray`).
- **Shape:** `(128, 128)` representing `(N_MELS, TIME_FRAMES)`.
- **Normalization:** Min-Max normalized to `[0.0, 1.0]` or standardized $z$-score depending on CNN training configuration:
  $$S_{\text{norm}} = \frac{S_{\text{dB}} - \min(S_{\text{dB}})}{\max(S_{\text{dB}}) - \min(S_{\text{dB}})}$$
- **Frequency Scale:** 128 triangular Mel filters linearly spaced between 0 Hz and 22,050 Hz (Nyquist).

### 1.3 Real-Time WebSocket Spectrogram Slice
- **Type:** JSON array of 128 float values: `[float, float, ..., float]`.
- **Value Range:** Normalized `0.0` to `1.0` representing current instantaneous power per Mel bin.

---

## 2. GeoJSON Specification for Pipeline Infrastructure

Pipelines and sensor assets are serialized according to standard RFC 7946 GeoJSON.

### 2.1 Pipeline Feature Format
```json
{
  "type": "Feature",
  "id": "PIPE-001",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [77.2090, 28.6139],
      [77.2140, 28.6175],
      [77.2185, 28.6210]
    ]
  },
  "properties": {
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
        "coordinates": [77.2090, 28.6139]
      },
      {
        "sensor_id": "SENSOR-A2",
        "chainage_meters": 1250.0,
        "coordinates": [77.2185, 28.6210]
      }
    ],
    "created_at": "2026-11-01T00:00:00.000Z",
    "updated_at": "2026-11-07T10:55:00.000Z"
  }
}
```

### 2.2 Leak Incident Point Feature (TDoA Localization Output)
```json
{
  "type": "Feature",
  "id": "LEAK-LOC-0001",
  "geometry": {
    "type": "Point",
    "coordinates": [77.2121, 28.6162]
  },
  "properties": {
    "alert_id": "ALT-2026-0001",
    "pipeline_id": "PIPE-001",
    "estimated_chainage_meters": 412.5,
    "uncertainty_radius_meters": 15.0,
    "severity": "WARNING",
    "class_label": "PINHOLE_LEAK",
    "confidence": 0.9425
  }
}
```

---

## 3. Database Entity Formats (SQLite)

### 3.1 Pipelines Entity (`pipelines`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `TEXT` | `PRIMARY KEY` | Pipeline ID (e.g. `"PIPE-001"`) |
| `name` | `TEXT` | `NOT NULL` | Human-readable pipeline section name |
| `material` | `TEXT` | `NOT NULL` | Ductile Iron, PVC, HDPE, Cast Iron, Steel |
| `diameter_mm` | `REAL` | `NOT NULL` | Internal pipe diameter in millimeters |
| `length_meters` | `REAL` | `NOT NULL` | Length in meters |
| `status` | `TEXT` | `NOT NULL` | `"NORMAL"`, `"WARNING"`, `"CRITICAL"`, `"OFFLINE"` |
| `coordinates_json` | `TEXT` | `NOT NULL` | Serialized GeoJSON LineString |
| `created_at` | `TEXT` | `NOT NULL` | ISO 8601 UTC string |
| `updated_at` | `TEXT` | `NOT NULL` | ISO 8601 UTC string |

### 3.2 Alerts Entity (`alerts`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `TEXT` | `PRIMARY KEY` | UUID string (e.g. `"ALT-2026-0001"`) |
| `pipeline_id` | `TEXT` | `FOREIGN KEY` | Reference to `pipelines.id` |
| `sensor_id` | `TEXT` | `NOT NULL` | Sensor ID detecting the event |
| `timestamp` | `TEXT` | `NOT NULL` | ISO 8601 UTC timestamp |
| `class_id` | `INTEGER` | `NOT NULL` | 0 (`NORMAL_FLOW`), 1 (`AMBIENT_URBAN`), 2 (`PINHOLE_LEAK`), 3 (`CAVITATION_BURST`) |
| `class_label` | `TEXT` | `NOT NULL` | Classification label |
| `confidence` | `REAL` | `NOT NULL` | Prediction probability score (0.0 to 1.0) |
| `dominant_frequency_hz` | `REAL` | `NOT NULL` | Dominant frequency in Hz |
| `sound_level_db` | `REAL` | `NOT NULL` | RMS sound pressure level in dBFS |
| `severity` | `TEXT` | `NOT NULL` | `"NONE"`, `"INFO"`, `"WARNING"`, `"CRITICAL"` |
| `estimated_chainage_meters` | `REAL` | `NULLABLE` | Distance along pipe if dual-sensor localized |
| `is_acknowledged` | `INTEGER` | `DEFAULT 0` | 0 for unacknowledged, 1 for acknowledged |
| `ticket_id` | `TEXT` | `FOREIGN KEY` | Reference to `work_order_tickets.id` |

### 3.3 Work Order Tickets Entity (`work_order_tickets`)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `TEXT` | `PRIMARY KEY` | Ticket identifier (e.g. `"WO-2026-0001"`) |
| `alert_id` | `TEXT` | `UNIQUE, FOREIGN KEY` | Source alert ID |
| `pipeline_id` | `TEXT` | `FOREIGN KEY` | Target pipeline ID |
| `priority` | `TEXT` | `NOT NULL` | `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"` |
| `status` | `TEXT` | `NOT NULL` | `"OPEN"`, `"DISPATCHED"`, `"IN_PROGRESS"`, `"RESOLVED"`, `"CLOSED"` |
| `assigned_crew` | `TEXT` | `NULLABLE` | Maintenance repair crew name |
| `description` | `TEXT` | `NOT NULL` | Repair details and observations |
| `estimated_latitude` | `REAL` | `NULLABLE` | Estimated GPS latitude |
| `estimated_longitude` | `REAL` | `NULLABLE` | Estimated GPS longitude |
| `estimated_chainage_meters` | `REAL` | `NULLABLE` | Chainage along pipe |
| `created_at` | `TEXT` | `NOT NULL` | ISO 8601 creation time |
| `updated_at` | `TEXT` | `NOT NULL` | ISO 8601 last update time |

