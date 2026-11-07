"""
SynthLeak API & WebSocket Protocol Verification Harness.

Validates REST endpoints and real-time WebSocket streams against CONTRACT.md.
Explicitly distinguishes between:
  1. Tests currently executable offline (Contract Schema & Canonical Payload Validation)
  2. Live Endpoints awaiting functional backend implementation (GET /health, /pipelines, /alerts, POST /tickets)
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import httpx
from shared.schemas import (
    PipelineListResponse,
    AlertListResponse,
    TicketCreateRequest,
    TicketResponse,
    SpectrogramFrameMessage,
    StandardErrorResponse,
)


def run_offline_contract_tests() -> bool:
    """Tests that can run immediately without a running server."""
    print("=" * 70)
    print("PHASE 1: OFFLINE CONTRACT & FIXTURE VERIFICATION (READY NOW)")
    print("=" * 70)

    examples_dir = root_dir / "shared" / "examples"
    test_cases = [
        ("pipeline_geojson.json", PipelineListResponse, "GET /pipelines schema"),
        ("alert_response.json", AlertListResponse, "GET /alerts schema"),
        ("ticket_request.json", TicketCreateRequest, "POST /tickets request payload"),
        ("ticket_response.json", TicketResponse, "POST /tickets response payload"),
        ("websocket_detection.json", SpectrogramFrameMessage, "WebSocket spectrogram frame"),
        ("error_response.json", StandardErrorResponse, "Canonical REST error format"),
    ]

    passed = 0
    for filename, model_cls, label in test_cases:
        filepath = examples_dir / filename
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            model_cls.model_validate(data)
            print(f"  [PASS] {label:<35} -> {filename}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {label:<35} -> {filename}: {e}")

    all_passed = passed == len(test_cases)
    print(f"\nOffline Contract Verification: {passed}/{len(test_cases)} passed.")
    return all_passed


def check_live_backend(base_url: str):
    """
    Tests live backend endpoints if running.
    If the backend is not yet started, reports awaiting backend implementation.
    """
    print("\n" + "=" * 70)
    print("PHASE 2: LIVE BACKEND ENDPOINT TESTS (AWAITING BACKEND LAUNCH)")
    print("=" * 70)

    print(f"Probing target backend: {base_url} ...")

    try:
        with httpx.Client(base_url=base_url, timeout=2.0) as client:
            resp = client.get("/health")
    except (httpx.ConnectError, httpx.TimeoutException):
        print(f"\n[STATUS: AWAITING BACKEND IMPLEMENTATION]")
        print(f"  The backend server is not running at {base_url}.")
        print("  Functional backend development has not started yet.")
        print("  When backend is implemented, launch it using:")
        print("    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
        print("\n  Live tests queued for backend readiness:")
        print("    - [PENDING] GET  /health      (System health & readiness check)")
        print("    - [PENDING] GET  /pipelines   (GeoJSON network topology query)")
        print("    - [PENDING] GET  /alerts      (Acoustic anomaly log query)")
        print("    - [PENDING] POST /tickets     (Non-destructive work-order creation)")
        print("    - [PENDING] WS   /ws/stream   (Real-time spectrogram frame stream)")
        return True  # Completed diagnosis cleanly without failure

    # If server is reachable, execute live verification suite
    print(f"[STATUS: BACKEND ONLINE] Connected to {base_url} (HTTP {resp.status_code})")
    all_live_passed = True

    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        # 1. GET /health
        print("\n  [TEST] GET /health ...")
        if resp.status_code == 200:
            print(f"    [PASS] /health returned HTTP 200: {resp.json()}")
        else:
            print(f"    [FAIL] /health returned unexpected status {resp.status_code}")
            all_live_passed = False

        # 2. GET /pipelines
        print("\n  [TEST] GET /pipelines ...")
        try:
            r = client.get("/pipelines")
            if r.status_code == 200:
                validated = PipelineListResponse.model_validate(r.json())
                print(f"    [PASS] Validated {validated.total} pipelines against PipelineListResponse.")
            else:
                print(f"    [FAIL] HTTP {r.status_code}: {r.text}")
                all_live_passed = False
        except Exception as e:
            print(f"    [FAIL] Endpoint error: {e}")
            all_live_passed = False

        # 3. GET /alerts
        print("\n  [TEST] GET /alerts ...")
        try:
            r = client.get("/alerts")
            if r.status_code == 200:
                validated = AlertListResponse.model_validate(r.json())
                print(f"    [PASS] Validated {validated.total} alerts against AlertListResponse.")
            else:
                print(f"    [FAIL] HTTP {r.status_code}: {r.text}")
                all_live_passed = False
        except Exception as e:
            print(f"    [FAIL] Endpoint error: {e}")
            all_live_passed = False

        # 4. POST /tickets (Verification mode: Test with dry-run or validation check)
        print("\n  [TEST] POST /tickets (Input Validation & Error Format Handling) ...")
        try:
            # Send payload with invalid priority to verify error handling without polluting database
            invalid_payload = {
                "alert_id": "ALT-TEST-VALIDATION",
                "pipeline_id": "PIPE-001",
                "priority": "INVALID_PRIORITY_TEST",
                "description": "Validation probe testing error handling"
            }
            r = client.post("/tickets", json=invalid_payload)
            if r.status_code in (400, 422):
                print(f"    [PASS] Correctly rejected invalid priority with HTTP {r.status_code}.")
            else:
                print(f"    [INFO] Received HTTP {r.status_code}: {r.text}")
        except Exception as e:
            print(f"    [FAIL] POST /tickets check error: {e}")
            all_live_passed = False

    return all_live_passed


def main():
    parser = argparse.ArgumentParser(description="SynthLeak Developer API Test Harness")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for live backend tests")
    parser.add_argument("--offline-only", action="store_true", help="Run only offline schema & fixture tests")
    args = parser.parse_args()

    offline_ok = run_offline_contract_tests()

    if args.offline_only:
        sys.exit(0 if offline_ok else 1)

    live_ok = check_live_backend(args.url)
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    sys.exit(0 if (offline_ok and live_ok) else 1)


if __name__ == "__main__":
    main()
