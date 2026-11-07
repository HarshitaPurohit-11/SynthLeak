"""
SynthLeak Shared Constants and System Parameters.
This module is the canonical Python reference for all audio, DSP, ML, and API constants.
All modules (ml, backend, scripts) must import from this file.
"""

# Audio Ingestion & DSP Parameters
SAMPLE_RATE: int = 44100
N_FFT: int = 1024
HOP_LENGTH: int = 512
N_MELS: int = 128
SPECTROGRAM_SHAPE: tuple[int, int] = (128, 128)
CLIP_SAMPLES: int = 65536  # 128 frames * 512 hop = 65536 samples (~1.486s)

# DSP Bandpass Filtering (Hz)
FILTER_LOW_CUT_HZ: float = 100.0
FILTER_HIGH_CUT_HZ: float = 10000.0
FILTER_URBAN_LOW_CUT_HZ: float = 500.0
FILTER_URBAN_HIGH_CUT_HZ: float = 9000.0

# 4-Class Acoustic Classification Taxonomy
CLASS_NORMAL_FLOW: int = 0
CLASS_AMBIENT_URBAN: int = 1
CLASS_PINHOLE_LEAK: int = 2
CLASS_CAVITATION_BURST: int = 3

CLASS_LABELS: dict[int, str] = {
    CLASS_NORMAL_FLOW: "NORMAL_FLOW",
    CLASS_AMBIENT_URBAN: "AMBIENT_URBAN",
    CLASS_PINHOLE_LEAK: "PINHOLE_LEAK",
    CLASS_CAVITATION_BURST: "CAVITATION_BURST",
}

LABEL_TO_CLASS_ID: dict[str, int] = {v: k for k, v in CLASS_LABELS.items()}

# Alert Severities
SEVERITY_NONE: str = "NONE"
SEVERITY_INFO: str = "INFO"
SEVERITY_WARNING: str = "WARNING"
SEVERITY_CRITICAL: str = "CRITICAL"

VALID_SEVERITIES: set[str] = {
    SEVERITY_NONE,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
}

# Work Order Ticket Priorities
PRIORITY_LOW: str = "LOW"
PRIORITY_MEDIUM: str = "MEDIUM"
PRIORITY_HIGH: str = "HIGH"
PRIORITY_CRITICAL: str = "CRITICAL"

VALID_PRIORITIES: set[str] = {
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
}

# Work Order Ticket Statuses
STATUS_OPEN: str = "OPEN"
STATUS_DISPATCHED: str = "DISPATCHED"
STATUS_IN_PROGRESS: str = "IN_PROGRESS"
STATUS_RESOLVED: str = "RESOLVED"
STATUS_CLOSED: str = "CLOSED"

VALID_TICKET_STATUSES: set[str] = {
    STATUS_OPEN,
    STATUS_DISPATCHED,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
    STATUS_CLOSED,
}

# Pipeline Operating Statuses
PIPELINE_STATUS_NORMAL: str = "NORMAL"
PIPELINE_STATUS_WARNING: str = "WARNING"
PIPELINE_STATUS_CRITICAL: str = "CRITICAL"
PIPELINE_STATUS_OFFLINE: str = "OFFLINE"

VALID_PIPELINE_STATUSES: set[str] = {
    PIPELINE_STATUS_NORMAL,
    PIPELINE_STATUS_WARNING,
    PIPELINE_STATUS_CRITICAL,
    PIPELINE_STATUS_OFFLINE,
}

# WebSocket Configuration
WS_STREAM_PATH: str = "/ws/stream"
WS_TARGET_FPS: int = 15  # Target frame rate for WebSocket transmission (10-20 FPS)

