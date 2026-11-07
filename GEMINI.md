# Antigravity Assistant Directives: SynthLeak

## Project Information
- **Project:** SynthLeak
- **Domain:** Real-Time Acoustic Pipe Leak Detection & Water Infrastructure Monitoring
- **Active Role:** Backend & Infrastructure Lead

---

## Authoritative Documentation
1. [`CONTRACT.md`](CONTRACT.md): Canonical interface specifications, schemas, audio constants, and classification taxonomy.
2. [`PROJECT_GUIDELINES.md`](PROJECT_GUIDELINES.md): Architectural standards and engineering guidelines.
3. [`CONTRIBUTING.md`](CONTRIBUTING.md): Git workflow, contract change protocol, and testing expectations.
4. [`shared/`](shared/): Pydantic schemas, constants, and canonical JSON fixtures.

---

## Operational Constraints

1. **Contract Adherence:** Code bridging system boundaries must conform strictly to `CONTRACT.md`.
2. **Domain Boundaries:**
   - Acoustic Signal Processing & ML: `ml/`, `audio-engine/dsp/`
   - Frontend & GIS Development: `frontend/`
   - Backend & Infrastructure: `backend/`, `audio-engine/capture.py`, Docker
   - Demo Production & Documentation: `demo/`, `data/`, `scripts/`
3. **Git Safety:**
   - Do not run `git commit`, `git push`, `git checkout -b`, `git branch -D`, `git reset --hard`, or `git clean -fd`.
   - Never push to any branch other than `main` (and only with explicit user instruction).
   - Leave all generated changes available locally for review.
4. **Audio Constants:**
   - Sample rate: 44,100 Hz
   - FFT size: 1,024
   - Hop length: 512
   - Mel bins: 128
   - Spectrogram dimension: (128, 128)
   - Classes: `0: NORMAL_FLOW`, `1: AMBIENT_URBAN`, `2: PINHOLE_LEAK`, `3: CAVITATION_BURST`
5. **No Hardcoded Metrics:** Real-time pipelines must report computed values. Synthetic test payloads must include `"is_simulated": true`.
