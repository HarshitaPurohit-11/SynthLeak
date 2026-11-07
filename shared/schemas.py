"""
SynthLeak Shared Pydantic Schemas.
Authoritative Python data models implementing the contracts in CONTRACT.md.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from shared.constants import (
    CLASS_LABELS,
    VALID_SEVERITIES,
    VALID_PRIORITIES,
    VALID_TICKET_STATUSES,
    VALID_PIPELINE_STATUSES,
    N_MELS,
)


# ==============================================================================
# ML Inference Interface (Acoustic Signal Processing & ML -> Backend & Infrastructure)
# ==============================================================================

class InferenceOutput(BaseModel):
    """Prediction output schema produced by the ML inference callable."""
    class_id: int = Field(..., ge=0, le=3, description="Classification category code (0..3)")
    class_label: str = Field(..., description="Classification label corresponding to class_id")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Softmax confidence probability (0.0 to 1.0)")
    peak_frequency_hz: float = Field(..., ge=0.0, description="Dominant spectral peak frequency in Hz")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of prediction")

    @model_validator(mode="after")
    def verify_class_consistency(self) -> "InferenceOutput":
        expected_label = CLASS_LABELS.get(self.class_id)
        if expected_label != self.class_label:
            raise ValueError(
                f"Mismatch between class_id ({self.class_id}) and class_label ('{self.class_label}'). "
                f"Expected '{expected_label}'."
            )
        return self


# ==============================================================================
# Real-Time Dashboard Stream (Backend & Infrastructure -> Frontend & GIS Development) [WebSocket]
# ==============================================================================

class ClassificationSummary(BaseModel):
    """Classification segment embedded in WebSocket frames."""
    class_id: int = Field(..., ge=0, le=3)
    class_label: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    dominant_frequency_hz: float = Field(..., ge=0.0)


class AlertSummary(BaseModel):
    """Alert evaluation embedded in WebSocket frames."""
    is_alert: bool = Field(..., description="True if leak detected (class 2 or 3)")
    severity: str = Field(..., description="NONE, INFO, WARNING, CRITICAL")
    message: str = Field(..., description="Human-readable alert summary")

    @model_validator(mode="after")
    def verify_severity(self) -> "AlertSummary":
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{self.severity}'. Must be one of {VALID_SEVERITIES}")
        return self


class SpectrogramFrameMessage(BaseModel):
    """Continuous real-time audio frame streamed over WebSocket at 10-20 FPS."""
    message_type: Literal["spectrogram_frame"] = "spectrogram_frame"
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    pipeline_id: str = Field(..., description="Monitored pipeline ID")
    sensor_id: str = Field(..., description="Sensor unit identifier")
    spectrogram_frame: List[float] = Field(
        ...,
        description=f"Array of exactly {N_MELS} normalized Mel bin energies (0.0 to 1.0)"
    )
    classification: ClassificationSummary = Field(..., description="Inference result")
    sound_level_db: float = Field(..., description="Instantaneous RMS sound level in dBFS")
    alert: AlertSummary = Field(..., description="Alert status")

    @model_validator(mode="after")
    def verify_frame_length(self) -> "SpectrogramFrameMessage":
        if len(self.spectrogram_frame) != N_MELS:
            raise ValueError(
                f"spectrogram_frame length must be exactly {N_MELS}, got {len(self.spectrogram_frame)}"
            )
        return self


class HeartbeatMessage(BaseModel):
    """Keepalive ping message on WebSocket."""
    message_type: Literal["heartbeat"] = "heartbeat"
    timestamp: str = Field(...)
    status: str = Field(default="OK")
    active_clients: int = Field(default=1, ge=0)


# ==============================================================================
# Interface C: REST APIs
# ==============================================================================

# --- GET /pipelines ---

class SensorMetadata(BaseModel):
    """Sensor location and metadata along pipeline."""
    sensor_id: str
    chainage_meters: float = Field(..., ge=0.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class LineStringGeometry(BaseModel):
    """GeoJSON LineString geometry."""
    type: Literal["LineString"] = "LineString"
    coordinates: List[List[float]] = Field(..., description="List of [lon, lat] pairs")


class PipelineItem(BaseModel):
    """Pipeline model returned in GET /pipelines."""
    pipeline_id: str
    name: str
    material: str
    diameter_mm: float = Field(..., gt=0.0)
    length_meters: float = Field(..., gt=0.0)
    status: str
    sensors: List[SensorMetadata] = Field(default_factory=list)
    geometry: LineStringGeometry
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def verify_pipeline_status(self) -> "PipelineItem":
        if self.status not in VALID_PIPELINE_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of {VALID_PIPELINE_STATUSES}")
        return self


class PipelineListResponse(BaseModel):
    """Response envelope for GET /pipelines."""
    total: int = Field(..., ge=0)
    items: List[PipelineItem]


# --- GET /alerts ---

class AlertItem(BaseModel):
    """Alert record returned in GET /alerts."""
    alert_id: str
    pipeline_id: str
    sensor_id: str
    timestamp: str
    class_id: int = Field(..., ge=0, le=3)
    class_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    dominant_frequency_hz: float = Field(..., ge=0.0)
    sound_level_db: float
    severity: str
    estimated_chainage_meters: Optional[float] = None
    is_acknowledged: bool = False
    ticket_id: Optional[str] = None

    @model_validator(mode="after")
    def verify_alert_fields(self) -> "AlertItem":
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{self.severity}'. Must be one of {VALID_SEVERITIES}")
        expected_label = CLASS_LABELS.get(self.class_id)
        if expected_label != self.class_label:
            raise ValueError(f"class_label '{self.class_label}' does not match class_id {self.class_id}")
        return self


class AlertListResponse(BaseModel):
    """Response envelope for GET /alerts."""
    total: int = Field(..., ge=0)
    items: List[AlertItem]


# --- POST /tickets ---

class LocationEstimate(BaseModel):
    """Geographic and chainage location estimate for leak repair."""
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    chainage_meters: Optional[float] = Field(None, ge=0.0)


class TicketCreateRequest(BaseModel):
    """Request payload for POST /tickets."""
    alert_id: str = Field(..., description="ID of the alert generating this work order")
    pipeline_id: str = Field(..., description="ID of the pipeline requiring maintenance")
    priority: str = Field(..., description="Ticket priority: LOW, MEDIUM, HIGH, CRITICAL")
    assigned_crew: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=5, max_length=500)
    location_estimate: Optional[LocationEstimate] = None

    @model_validator(mode="after")
    def verify_priority(self) -> "TicketCreateRequest":
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be one of {VALID_PRIORITIES}")
        return self


class TicketResponse(BaseModel):
    """Created ticket object returned by POST /tickets."""
    ticket_id: str
    alert_id: str
    pipeline_id: str
    priority: str
    status: str
    assigned_crew: Optional[str] = None
    description: str
    location_estimate: Optional[LocationEstimate] = None
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def verify_ticket_fields(self) -> "TicketResponse":
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be one of {VALID_PRIORITIES}")
        if self.status not in VALID_TICKET_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of {VALID_TICKET_STATUSES}")
        return self


# --- Standard Error Response ---

class ErrorDetail(BaseModel):
    """Specific field-level validation or domain error detail."""
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    """Body of structured API error response."""
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: str


class StandardErrorResponse(BaseModel):
    """Standard error response format for all REST endpoints."""
    error: ErrorBody

