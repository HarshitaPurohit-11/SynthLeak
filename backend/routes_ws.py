"""
SynthLeak Real-Time Streaming & WebSocket Endpoint.
Streams continuous 128-bin Mel spectrogram frames, instantaneous dBFS levels,
and anomaly alerts at 10-20 FPS (CONTRACT.md).

Leverages audio-engine/dsp/spectrogram.py for canonical Mel frame extraction
and ml/classifier.py for trained PyTorch CNN inference.
"""

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.websocket_manager import ws_manager
from backend.audio_buffer import CircularAudioBuffer
from backend.simulation import ScenarioReplayer
from backend.ml_adapter import MLInferenceAdapter
from backend.services import AlertService
from backend.database import SessionLocal
import sys
from pathlib import Path

# Add audio-engine to sys.path so 'dsp' can be imported cleanly
_audio_engine_dir = Path(__file__).resolve().parent.parent / "audio-engine"
if str(_audio_engine_dir) not in sys.path:
    sys.path.insert(0, str(_audio_engine_dir))

from dsp.spectrogram import mel_frames_normalized, rms_dbfs, dominant_frequency_hz
from shared.constants import (
    WS_STREAM_PATH,
    WS_TARGET_FPS,
    CLIP_SAMPLES,
    N_MELS,
    SAMPLE_RATE,
)
from shared.schemas import (
    SpectrogramFrameMessage,
    ClassificationSummary,
    AlertSummary,
    HeartbeatMessage,
)

router = APIRouter(tags=["WebSocket Stream"])

# Module-level instances for streaming loop
global_audio_buffer = CircularAudioBuffer()
global_scenario_replayer = ScenarioReplayer()
global_ml_adapter = MLInferenceAdapter()

# Hardware audio capture manager with automatic fallback to synthetic replayer
try:
    from capture import AudioCaptureDevice
    global_audio_capture = AudioCaptureDevice(buffer=global_audio_buffer)
    global_audio_capture.start_capture()
except Exception:
    global_audio_capture = None


@router.websocket(WS_STREAM_PATH)
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    Continuous real-time audio telemetry and anomaly detection WebSocket stream.
    Broadcasts at ~15 FPS conforming strictly to SpectrogramFrameMessage schema.
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Check for incoming client messages (e.g. heartbeat pings or test trigger commands)
            try:
                # Non-blocking poll for incoming client message
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.01)
                action = data.get("action") or data.get("type") or data.get("message_type")
                if action in ("ping", "heartbeat"):
                    pong = HeartbeatMessage(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        status="OK",
                        active_clients=ws_manager.client_count,
                    )
                    await websocket.send_json(pong.model_dump())
            except (asyncio.TimeoutError, TimeoutError):
                pass
            except WebSocketDisconnect:
                break
            except Exception:
                pass

            # Generate real-time frame
            frame_delay = 1.0 / WS_TARGET_FPS
            chunk_seconds = frame_delay

            if global_audio_capture and global_audio_capture.is_capturing:
                # Real hardware audio is capturing into global_audio_buffer
                latest_chunk = global_audio_buffer.get_latest(CLIP_SAMPLES)
                samples = latest_chunk[-int(SAMPLE_RATE * chunk_seconds):]
                class_hint = None
                is_sim = False
            else:
                # Simulation mode: scenario replayer feeds acoustic pipeline
                samples, class_id, class_label = global_scenario_replayer.get_next_chunk(chunk_seconds)
                global_audio_buffer.write(samples)
                latest_chunk = global_audio_buffer.get_latest(CLIP_SAMPLES)
                class_hint = class_id
                is_sim = True

            # Compute DSP metrics using audio-engine/dsp routines
            mel_matrix = mel_frames_normalized(latest_chunk)
            # Pick the most recent normalized 128-bin Mel frame (shape: frames, 128)
            mel_frame = [round(float(v), 4) for v in mel_matrix[-1].tolist()] if len(mel_matrix) > 0 else [0.0] * N_MELS
            sound_level = rms_dbfs(samples)
            dom_freq = dominant_frequency_hz(samples)

            # Run ML classification adapter (using trained PyTorch CNN weights)
            pred = await asyncio.to_thread(
                global_ml_adapter.predict,
                raw_audio=latest_chunk,
                dominant_freq=dom_freq,
                hint_class=class_hint,
            )

            # Evaluate alert severity
            is_alert, severity, message = AlertService.evaluate_severity(pred.class_id, sound_level)

            # If critical/warning leak event, persist alert in DB
            if is_alert and severity in ("WARNING", "CRITICAL"):
                try:
                    with SessionLocal() as db:
                        AlertService.create_alert(
                            db=db,
                            pipeline_id="PIPE-001",
                            sensor_id="SEN-001",
                            class_id=pred.class_id,
                            class_label=pred.class_label,
                            confidence=pred.confidence,
                            dominant_freq=dom_freq,
                            sound_level_db=sound_level,
                            estimated_chainage=345.5,
                        )
                except Exception:
                    pass

            # Construct verified WebSocket message frame
            now_iso = datetime.now(timezone.utc).isoformat()
            frame_msg = SpectrogramFrameMessage(
                message_type="spectrogram_frame",
                timestamp=now_iso,
                pipeline_id="PIPE-001",
                sensor_id="SEN-001",
                spectrogram_frame=mel_frame,
                classification=ClassificationSummary(
                    class_id=pred.class_id,
                    class_label=pred.class_label,
                    confidence=pred.confidence,
                    dominant_frequency_hz=dom_freq,
                ),
                sound_level_db=sound_level,
                alert=AlertSummary(
                    is_alert=is_alert,
                    severity=severity,
                    message=message,
                ),
            )

            frame_payload = frame_msg.model_dump()
            if is_sim:
                frame_payload["is_simulated"] = True

            await websocket.send_json(frame_payload)
            await asyncio.sleep(frame_delay)

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await ws_manager.disconnect(websocket)
