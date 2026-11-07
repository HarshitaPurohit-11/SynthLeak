# Development Standards, Git Workflow & Governance

## 1. Core Engineering Principles

1. **Contract-First Development:** Code that interfaces across subsystems must strictly adhere to [`CONTRACT.md`](../CONTRACT.md). Field names, data types, and status codes are canonical.
2. **Domain Boundaries:** Respect module ownership and directory assignments:
   - **Acoustic Signal Processing & ML:** `ml/`, `audio-engine/dsp/`
   - **Frontend & GIS Development:** `frontend/`
   - **Backend & Infrastructure:** `backend/`, `audio-engine/capture.py`, Docker configuration
   - **Demo Production & Documentation:** `demo/`, `data/`, `scripts/`
3. **Preserve Working Logic:** Inspect existing code, docstrings, and tests before modifying files.
4. **Import Shared Constants:** Import system parameters from [`shared/constants.py`](../shared/constants.py) (e.g. `SAMPLE_RATE = 44100`, `N_FFT = 1024`, `HOP_LENGTH = 512`, `N_MELS = 128`).
5. **Metric Integrity:** Do not present static or hardcoded values as live sensor measurements. Synthetic test payloads must include `"is_simulated": true`.
6. **Standard Terminology:** Always write **Adaptive Noise Suppression (ANS)**. Never use "Active Noise Cancellation".

---

## 2. Git Workflow & Permission Governance

### 2.1 Git Operations Authorization
- **Permitted Operations:**
  - Cloning repository (`git clone`).
  - Checking status and diffs (`git status`, `git diff`, `git log`).
  - Local file editing, validation, and testing.
- **Strictly Prohibited Operations (Unless Explicitly Authorized by Lead):**
  - `git commit`
  - `git push`
  - `git branch` (creation or deletion)
  - `git checkout` / `git switch`
  - Modifying git remotes
- **Permanently Forbidden Destructive Operations:**
  - `git reset --hard`
  - `git clean -fd`
  - `git push --force`

### 2.2 Branch & Push Policy
- **Target Branch:** All authorized pushes must target `main` only.
- **Pre-Push Verification:**
  1. Inspect `git status` and ensure the working tree is in an expected state.
  2. Inspect `git diff` to review all staged and unstaged modifications.
  3. Run validation tests (`python scripts/validate_contracts.py`).
  4. Obtain explicit human lead approval.
- **Credentials:** Each developer authenticates using their own Git credentials. Never store credentials or access tokens in repository files.

---

## 3. Contract Change Protocol

When an endpoint, data model, or audio parameter must be updated, follow the structured procedure in [`CONTRIBUTING.md`](../CONTRIBUTING.md#3-contract-change-protocol):
1. Document the proposed modification and rationale.
2. Identify all affected subsystems (e.g. ML, Backend, Frontend).
3. Verify backward compatibility with existing clients.
4. Obtain consensus from affected engineering leads.
5. Update canonical artifacts:
   - `CONTRACT.md`
   - `shared/constants.py` and `shared/schemas.py`
   - `shared/examples/*.json`
6. Run `python scripts/validate_contracts.py`.
7. Implement updates in subsystem codebases.

---

## 4. Technical Consistency Guidelines

### 4.1 Filter Discrepancy Resolution
- Architecture documentation specifies a bandpass filter of **100 Hz to 10 kHz**.
- Initial prototype DSP code used **500 Hz to 9 kHz**.
- **Resolution:** The Acoustic Signal Processing & ML team maintains ownership of internal DSP filter cutoffs. The platform contract designates **100 Hz to 10 kHz** as the system-wide baseline bandpass range, with **500 Hz to 9 kHz** accepted as an active noise-suppression preset for high-vibration urban environments. The backend accepts predictions agnostic of internal filter cutoffs.

### 4.2 Real-Time Integration Buffer Management
- Audio buffer size: Fixed sliding window of 65,536 samples (1.486 sec at 44.1 kHz).
- Lockless circular ring buffer implementation in the backend audio capture worker.
- Inference execution: Handled via `asyncio.to_thread` to prevent blocking the WebSocket broadcast loop.
- WebSocket streaming rate: Throttled to 10–20 FPS to ensure smooth rendering on the frontend without saturating the browser event loop.

---

## 5. Coding & Linting Conventions

- **Python (Backend, ML, Shared):**
  - Python 3.10+
  - PEP 8 compliance, formatted with `black` or `ruff`.
  - Type hinting on all public function signatures.
  - Logging via `logging.getLogger(__name__)`, avoiding raw `print()` statements in production services.
- **TypeScript / React (Frontend):**
  - Functional React components with hooks.
  - TypeScript interfaces for all component props.
  - Tailwind CSS utility classes for styling.
  - Clean separation between visual UI components and WebSocket state hooks.
