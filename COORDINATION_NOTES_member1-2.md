# Coordination notes from Members 1 and 2 (ML/DSP + Frontend)

Nothing in `shared/`, `CONTRACT.md` or the other members' folders was modified. Items below need a teammate's action
or a decision. None of them is a contract change unless marked **(proposal)**.

## For Member 3 (Backend & Infrastructure)
1. **Use the real classifier:** `from ml.classifier import LeakClassifier`; `clf = LeakClassifier()`; call
   `clf.predict(buffer_65536_float32)` inside `asyncio.to_thread`. Importing `ml.*` puts `audio-engine/` on `sys.path`
   automatically (the hyphenated folder is not an importable package), so `dsp` imports work without extra setup.
   It returns exactly the `InferenceOutput` dict; it raises `ValueError` / `RuntimeError` as CONTRACT.md 4.4 describes.
2. **Dependencies:** `requirements.txt` does not contain PyTorch. Add `torch` (CPU build is fine) to the backend image,
   e.g. `pip install torch --index-url https://download.pytorch.org/whl/cpu` in the Dockerfile. `ml/requirements-ml.txt`
   lists the ML extras (matplotlib is only needed for `ml.evaluate`).
3. **Weights:** `ml/weights/leak_cnn.pt` (about 1 MB) is committed so the backend works out of the box. Without it,
   `predict()` raises `RuntimeError("Model weights not found ...")`.
4. **WebSocket `spectrogram_frame` values:** use `dsp.spectrogram.mel_frames_normalized(audio)` (shape `(frames, 128)`,
   values 0-1) and send one row per message at ~15 FPS; `dsp.spectrogram.rms_dbfs(audio)` gives `sound_level_db`.
   Use the classification from the same `predict()` call for the embedded `classification` block.
5. **Adaptive Noise Suppression:** `LeakClassifier(use_ans=True)` plus `clf.calibrate(background_clip)` (a leak-free clip
   from the same sensor, e.g. at install time). ANS is a no-op until calibrated. Do not auto-calibrate from live audio
   unless the model said NORMAL/AMBIENT, otherwise a leak can be learned as "background".
6. **CORS / proxy:** the dashboard uses a same-origin proxy (Vite in dev, nginx in Docker), so CORS is not required.
   `frontend/nginx.conf` expects the compose service to be named `backend`.
7. **Endpoints the UI relies on:** `GET /health`, `GET /pipelines?limit=200`, `GET /alerts?limit=50`, `POST /tickets`
   (409 `CONFLICT` is handled), WebSocket `/ws/stream`.

## For Member 4 (Demo & Documentation)
- `python -m ml.export_demo_clips` writes synthetic WAVs (git-ignored) usable for scenario replay.
- Real recordings: put WAVs under `data/sample_audio/` with the class keyword in the folder or file name
  (`leak`/`pinhole`/`hiss`/`bottle`, `normal`/`flow`, `ambient`/`traffic`/`urban`/`silence`/`noise`,
  `burst`/`cavitation`/`hammer`/`pump`). Then `python -m ml.training.train --real-dir data/sample_audio` and
  `python -m ml.evaluate --real-dir data/sample_audio` report real-audio numbers separately.
- Validation figures for the slides: `ml/reports/` (`metrics_summary.md`, `confusion_matrix.png`, `accuracy_vs_snr.png`).
  These are measured on SYNTHETIC data and must be described that way.

## Decisions / proposals for the team
- **(proposal)** The work-split plan mentions an "estimated orifice size" and a noise-filter toggle that reaches the
  model. The contract has no field or endpoint for either, so the UI shows neither as a measurement and the toggle is
  display-only. If wanted, propose via the Contract Change Protocol: an optional `estimated_orifice_mm` in the alert
  (only if computed by a validated method) and a `POST /settings {noise_suppression: bool}`.
- Git: `AGENTS.md` / `CONTRIBUTING.md` say pushes go to `main` and no uncoordinated branches. Follow that unless the
  team agrees otherwise.
