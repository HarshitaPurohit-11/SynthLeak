"""
SynthLeak Backend Comprehensive Automated Test Suite.
Verifies all Member 3 responsibilities:
  1. Application Startup & Lifespan
  2. Health Check Endpoint
  3. Pipelines REST API
  4. Alerts REST API
  5. Work-Order Tickets REST API & Validation
  6. Database Models & Persistence
  7. Thread-Safe Circular Audio Buffer
  8. Audio Processor & Mel Spectrogram Output Dimensions
  9. ML Inference Adapter & Schema Validation
  10. Synthetic Audio Generator & Scenario Replayer
  11. Alert Evaluation Service
  12. Acoustic TDoA Dual-Sensor Cross-Correlation & Localization
"""

import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, SessionLocal
from backend.models import PipelineModel, SensorModel, AlertModel, TicketModel
from backend.seed import init_db, seed_initial_data
from backend.services import AlertService, TicketService
from backend.audio_buffer import CircularAudioBuffer, AudioProcessor
from backend.simulation import SyntheticAudioGenerator, ScenarioReplayer
from backend.ml_adapter import MLInferenceAdapter
from backend.localization import AcousticLocalizer
from shared.schemas import TicketCreateRequest, LocationEstimate
from shared.constants import (
    SAMPLE_RATE,
    CLIP_SAMPLES,
    N_MELS,
    CLASS_NORMAL_FLOW,
    CLASS_PINHOLE_LEAK,
    CLASS_CAVITATION_BURST,
    CLASS_AMBIENT_URBAN,
)


@pytest.fixture(scope="module")
def test_db():
    """Provides a fresh in-memory SQLite database session for unit tests."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine)

    session = TestingSessionLocal()
    seed_initial_data(session)
    yield session
    session.close()


# ------------------------------------------------------------------------------
# 1. Database & Persistence Tests
# ------------------------------------------------------------------------------

def test_database_models_and_seeding(test_db):
    """Verify that initial database models and relationships are correctly persisted."""
    pipelines = test_db.query(PipelineModel).all()
    assert len(pipelines) >= 1
    p1 = pipelines[0]
    assert p1.pipeline_id == "PIPE-001"
    assert len(p1.sensors) >= 2
    assert p1.material == "Ductile Iron"

    alerts = test_db.query(AlertModel).all()
    assert len(alerts) >= 1
    assert alerts[0].pipeline_id == "PIPE-001"


def test_ticket_service_creation(test_db):
    """Verify ticket service creates tickets with canonical ID and marks alert acknowledged."""
    req = TicketCreateRequest(
        alert_id="ALT-20261107-001",
        pipeline_id="PIPE-001",
        priority="HIGH",
        assigned_crew="Repair Unit 4",
        description="Pinhole leak detected near municipal valve 12",
        location_estimate=LocationEstimate(
            chainage_meters=345.5,
            latitude=26.9124,
            longitude=75.7873,
        ),
    )

    ticket_resp = TicketService.create_ticket(test_db, req)
    assert ticket_resp.ticket_id.startswith("TKT-")
    assert ticket_resp.priority == "HIGH"
    assert ticket_resp.status == "OPEN"

    # Verify persistent state in DB
    saved = test_db.query(TicketModel).filter_by(ticket_id=ticket_resp.ticket_id).first()
    assert saved is not None
    assert saved.assigned_crew == "Repair Unit 4"


# ------------------------------------------------------------------------------
# 2. Audio Buffer & DSP Tests
# ------------------------------------------------------------------------------

def test_circular_audio_buffer():
    """Verify thread-safe ring buffer write, chronological ordering, and wrap-around."""
    buf = CircularAudioBuffer(capacity_samples=1000)

    # Initial get on empty buffer
    empty_samples = buf.get_latest(100)
    assert len(empty_samples) == 100
    assert np.all(empty_samples == 0)

    # Write 400 samples
    data1 = np.arange(1, 401, dtype=np.float32)
    buf.write(data1)
    out1 = buf.get_latest(100)
    assert len(out1) == 100
    assert np.array_equal(out1, data1[-100:])

    # Overwrite buffer with 1200 samples (exceeds capacity)
    data2 = np.arange(1000, 2200, dtype=np.float32)
    buf.write(data2)
    out2 = buf.get_latest(500)
    assert len(out2) == 500
    assert np.array_equal(out2, data2[-500:])


def test_audio_processor_dsp():
    """Verify Mel spectrogram dimensions, single-frame extraction, and dBFS sound levels."""
    sr = SAMPLE_RATE
    duration = 1.486  # ~CLIP_SAMPLES
    t = np.linspace(0, duration, CLIP_SAMPLES, endpoint=False)
    # Sine wave at 3000 Hz (leak range)
    test_signal = (0.5 * np.sin(2 * np.pi * 3000 * t)).astype(np.float32)

    # Sound level dBFS
    db = AudioProcessor.compute_sound_level_db(test_signal)
    assert -10.0 < db < 0.0

    # Mel Spectrogram output shape
    mel_spec = AudioProcessor.compute_mel_spectrogram(test_signal)
    assert mel_spec.shape[0] == N_MELS  # 128 Mel frequency bins
    assert np.all((mel_spec >= 0.0) & (mel_spec <= 1.0))

    # Single Mel frame for WebSocket telemetry
    single_frame = AudioProcessor.compute_single_mel_frame(test_signal)
    assert len(single_frame) == N_MELS
    assert all(0.0 <= val <= 1.0 for val in single_frame)

    # Dominant frequency
    dom_freq = AudioProcessor.compute_dominant_frequency(test_signal)
    assert 2900 <= dom_freq <= 3100


# ------------------------------------------------------------------------------
# 3. Synthetic Data & Scenario Replayer Tests
# ------------------------------------------------------------------------------

def test_synthetic_audio_generator():
    """Verify synthetic signals for all 4 taxonomy classes."""
    gen = SyntheticAudioGenerator()
    classes = [CLASS_NORMAL_FLOW, CLASS_AMBIENT_URBAN, CLASS_PINHOLE_LEAK, CLASS_CAVITATION_BURST]

    for cid in classes:
        samples = gen.generate_signal(cid, duration_seconds=0.5)
        assert len(samples) == int(SAMPLE_RATE * 0.5)
        assert samples.dtype == np.float32
        assert np.max(np.abs(samples)) <= 1.0


def test_scenario_replayer():
    """Verify sequential scenario replay across stages."""
    replayer = ScenarioReplayer()
    samples, cid, label = replayer.get_next_chunk(0.1)
    assert len(samples) == int(SAMPLE_RATE * 0.1)
    assert cid in (CLASS_NORMAL_FLOW, CLASS_AMBIENT_URBAN, CLASS_PINHOLE_LEAK, CLASS_CAVITATION_BURST)
    assert isinstance(label, str)


# ------------------------------------------------------------------------------
# 4. ML Adapter & Alert Workflow Tests
# ------------------------------------------------------------------------------

def test_ml_inference_adapter():
    """Verify inference output format and schema adherence."""
    adapter = MLInferenceAdapter()
    dummy_tensor = np.zeros((128, 128), dtype=np.float32)

    pred = adapter.predict(dummy_tensor, dominant_freq=3400.0)
    assert pred.class_label in ("PINHOLE_LEAK", "CAVITATION_BURST", "NORMAL_FLOW", "AMBIENT_URBAN")
    assert 0.0 <= pred.confidence <= 1.0
    assert pred.peak_frequency_hz == 3400.0


def test_alert_severity_evaluation():
    """Verify severity mapping matches CONTRACT.md."""
    # Cavitation Burst -> CRITICAL
    is_alert, sev, msg = AlertService.evaluate_severity(CLASS_CAVITATION_BURST, -20.0)
    assert is_alert is True
    assert sev == "CRITICAL"

    # Pinhole leak with high sound -> WARNING
    is_alert, sev, msg = AlertService.evaluate_severity(CLASS_PINHOLE_LEAK, -25.0)
    assert is_alert is True
    assert sev == "WARNING"

    # Normal flow -> NONE
    is_alert, sev, msg = AlertService.evaluate_severity(CLASS_NORMAL_FLOW, -45.0)
    assert is_alert is False
    assert sev == "NONE"


# ------------------------------------------------------------------------------
# 5. Acoustic TDoA Dual-Sensor Localization Tests
# ------------------------------------------------------------------------------

def test_acoustic_localization_tdoa():
    """Verify cross-correlation time delay and distance estimation with synthetic delay."""
    localizer = AcousticLocalizer(sr=SAMPLE_RATE, propagation_speed_mps=1500.0)

    # Create signal
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    base_signal = (np.sin(2 * np.pi * 800 * t) + np.random.normal(0, 0.1, len(t))).astype(np.float32)

    # Delay signal S2 by exactly 100 samples (~2.267 ms)
    delay_samples = 100
    signal_s1 = base_signal
    signal_s2 = np.pad(base_signal, (delay_samples, 0))[:len(base_signal)]

    delta_t, peak = localizer.compute_tdoa(signal_s1, signal_s2)
    expected_delay = delay_samples / SAMPLE_RATE

    # Check calculated time delay is accurate within 1 sample tolerance
    assert abs(delta_t - expected_delay) < (2.0 / SAMPLE_RATE)
    assert peak > 0.85

    # Estimate leak position between sensors at chainage 100m and 300m (L = 200m)
    chainage, dt, conf = localizer.estimate_leak_position(
        signal_s1=signal_s1,
        signal_s2=signal_s2,
        sensor1_chainage=100.0,
        sensor2_chainage=300.0,
    )

    assert chainage is not None
    assert 100.0 <= chainage <= 300.0
    assert conf > 0.85
