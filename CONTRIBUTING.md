# Contributing to SynthLeak

This guide outlines our development workflow, Git safety policies, contract change protocol, and testing expectations.

---

## 1. Development Principles

1. **Domain Autonomy:** Each contributor focuses on their designated discipline (`ml/`, `frontend/`, `backend/`, or `demo/`). Avoid modifying files outside your domain without coordination.
2. **Contract Compliance:** Any code interacting across system boundaries (ML inference, WebSocket streaming, REST APIs, database schemas) must conform strictly to [`CONTRACT.md`](CONTRACT.md).
3. **Preserve Working Logic:** Inspect existing code, docstrings, and tests before making modifications. Do not replace working implementations wholesale.
4. **Lean Dependencies:** Keep project dependencies minimal. Prefer the standard library and existing packages where possible.

---

## 2. Git Workflow & Safety Policies

- **Branch Policy:** Authorized code integrations target the `main` branch.
- **Review Prior to Integration:** Inspect `git status` and `git diff` before integrating changes.
- **Strictly Prohibited Operations:**
  - Never execute destructive commands such as `git reset --hard`, `git clean -fd`, or `git push --force`.
  - Do not create uncoordinated branches or switch branches unexpectedly during collaborative sessions.
  - Keep all local changes reviewed and validated before committing.
- **Authentication:** Contributors authenticate using their own configured Git credentials. Never commit credentials, API tokens, or secrets to the repository.

---

## 3. Contract Change Protocol

When an endpoint, schema, or system constant needs to be updated:

1. **Identify the Need:** Document why the interface must change and what benefits it provides.
2. **Assess Impact:** Identify every affected component (e.g. updating inference outputs impacts both ML and Backend; updating WebSocket frames impacts both Backend and Frontend).
3. **Verify Backward Compatibility:** Ensure the update does not break active frontend parsers or ingestion pipelines.
4. **Update Shared Specifications First:**
   - Update [`CONTRACT.md`](CONTRACT.md).
   - Update [`shared/constants.py`](shared/constants.py) and [`shared/schemas.py`](shared/schemas.py).
   - Update canonical payloads in [`shared/examples/`](shared/examples/).
5. **Run Schema Validation:**
   ```bash
   python scripts/validate_contracts.py
   ```
6. **Implement in Code:** Once the shared specifications pass validation, implement the changes in the corresponding module codebases.

---

## 4. Local Testing & Verification

Before submitting or reviewing code changes, run the appropriate test suites:

- **Contract & Schema Validation:**
  ```bash
  python scripts/validate_contracts.py
  ```
- **Backend Tests:**
  ```bash
  pytest backend/tests/
  ```
- **ML & DSP Tests:**
  ```bash
  pytest ml/tests/
  ```
- **Frontend Tests:**
  ```bash
  cd frontend && npm test
  ```
- **End-to-End API Test Harness:**
  ```bash
  python scripts/test_api.py
  ```

