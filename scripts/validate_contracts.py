"""
SynthLeak Shared Contract & Schema Validation Script.
Validates all canonical JSON examples against Pydantic schemas.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from shared.schemas import (
    InferenceOutput,
    SpectrogramFrameMessage,
    PipelineListResponse,
    AlertListResponse,
    TicketCreateRequest,
    TicketResponse,
    StandardErrorResponse,
)
from shared.constants import (
    SAMPLE_RATE,
    N_FFT,
    HOP_LENGTH,
    N_MELS,
    CLIP_SAMPLES,
    SPECTROGRAM_SHAPE,
    CLASS_LABELS,
)


def load_json(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def run_validations():
    print("=" * 60)
    print("SYNTHLEAK CONTRACT & SCHEMA VALIDATION")
    print("=" * 60)

    examples_dir = root_dir / "shared" / "examples"
    assert examples_dir.exists(), f"Examples directory missing: {examples_dir}"

    tests = [
        ("inference_output.json", InferenceOutput, "ML Inference Output"),
        ("websocket_detection.json", SpectrogramFrameMessage, "Real-Time Dashboard Stream Frame"),
        ("pipeline_geojson.json", PipelineListResponse, "GET /pipelines Response Envelope"),
        ("alert_response.json", AlertListResponse, "GET /alerts Response Envelope"),
        ("ticket_request.json", TicketCreateRequest, "POST /tickets Request Body"),
        ("ticket_response.json", TicketResponse, "POST /tickets Response Body"),
        ("error_response.json", StandardErrorResponse, "REST Standard Error Response"),
    ]

    passed = 0
    failed = 0

    for filename, schema_cls, description in tests:
        filepath = examples_dir / filename
        print(f"\n[TEST] Validating {filename} ({description})...")
        try:
            data = load_json(filepath)
            instance = schema_cls.model_validate(data)
            print(f"  -> SUCCESS: Validated against {schema_cls.__name__}")
            passed += 1
        except Exception as e:
            print(f"  -> FAILED: Validation error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("CHECKING SHARED AUDIO CONSTANTS...")
    print("=" * 60)
    assert SAMPLE_RATE == 44100, f"Invalid SAMPLE_RATE: {SAMPLE_RATE}"
    assert N_FFT == 1024, f"Invalid N_FFT: {N_FFT}"
    assert HOP_LENGTH == 512, f"Invalid HOP_LENGTH: {HOP_LENGTH}"
    assert N_MELS == 128, f"Invalid N_MELS: {N_MELS}"
    assert CLIP_SAMPLES == 65536, f"Invalid CLIP_SAMPLES: {CLIP_SAMPLES}"
    assert SPECTROGRAM_SHAPE == (128, 128), f"Invalid SPECTROGRAM_SHAPE: {SPECTROGRAM_SHAPE}"
    assert len(CLASS_LABELS) == 4, f"Invalid class label count: {len(CLASS_LABELS)}"
    print("  -> All audio constants match system blueprint exactly.")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed.")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_validations()

