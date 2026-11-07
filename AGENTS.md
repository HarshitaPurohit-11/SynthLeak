# Project Directives: SynthLeak

## Project Summary
SynthLeak is a real-time acoustic pipeline leak detection and localization platform for water distribution infrastructure. It integrates digital signal processing (Butterworth filtering and Adaptive Noise Suppression), continuous STFT Mel spectrogram generation, a 4-class CNN acoustic classifier, asynchronous WebSocket telemetry streaming, and a React Leaflet dashboard with work-order dispatch.

---

## Engineering Guidelines for AI Coding Assistants

1. **Follow the Shared Contract:** [`CONTRACT.md`](CONTRACT.md) is the canonical interface specification. All schemas, parameter names, data types, and status codes must match `CONTRACT.md` exactly.
2. **Respect Module Ownership:** Work strictly within assigned boundaries and do not modify files in other domains without explicit instructions:
   - **Acoustic Signal Processing & ML:** `ml/`, `audio-engine/dsp/`
   - **Frontend & GIS Development:** `frontend/`
   - **Backend & Infrastructure:** `backend/`, `audio-engine/capture.py`, `Dockerfile`, root orchestration
   - **Demo Production & Documentation:** `demo/`, `data/`, `scripts/`
3. **Import Shared Constants:** Import parameters from [`shared/constants.py`](shared/constants.py) (e.g. `SAMPLE_RATE = 44100`, `N_FFT = 1024`, `HOP_LENGTH = 512`, `N_MELS = 128`, 4-class taxonomy). Never hardcode audio parameters or class indices.
4. **Use Canonical Data Formats:** Use the JSON payloads defined in `CONTRACT.md` and verified in `shared/examples/`. Do not introduce improvised payload structures.
5. **Preserve Existing Code:** Inspect existing implementations, docstrings, and tests before modifying files. Preserve working logic.
6. **Maintain Backward Compatibility:** Any interface update must preserve backward compatibility for the frontend client and data ingestion pipelines.
7. **Verify With Tests:** Every new endpoint, schema validation, and DSP utility must include automated unit tests verifying contract compliance.
8. **Follow Contract Change Protocol:** When interface modifications are required, follow the process in [`CONTRIBUTING.md`](CONTRIBUTING.md#3-contract-change-protocol) before altering code.
9. **Technical Terminology:** Use **Adaptive Noise Suppression (ANS)**. Never use "Active Noise Cancellation".
10. **Metric Integrity:** Do not present static or hardcoded values as live telemetry measurements. Synthetic test payloads must include `"is_simulated": true`.
11. **Git Safety:** Do not execute unauthorized commits, pushes, branch creations, branch deletions, or destructive operations (`git reset --hard`, `git clean -fd`). Authorized pushes must target `main` only.
