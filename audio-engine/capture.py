"""
SynthLeak Hardware Audio Ingestion & Capture Adapter.
Owned by Backend & Infrastructure (AGENTS.md / CONTRACT.md).

Acquires audio samples from:
1. Physical soundcard / audio sensor hardware via sounddevice (if available).
2. Synthetic simulation / WAV replay (when hardware is unavailable).

Directly pipes 44.1 kHz PCM audio frames into the CircularAudioBuffer.
"""

import logging
import threading
from typing import Optional, Callable
import numpy as np

from shared.constants import SAMPLE_RATE, CLIP_SAMPLES
from backend.audio_buffer import CircularAudioBuffer

logger = logging.getLogger("synthleak.capture")


class AudioCaptureDevice:
    """
    Hardware and streaming audio capture manager.
    Connects acoustic microphone input to the thread-safe circular ring buffer.
    """

    def __init__(
        self,
        buffer: Optional[CircularAudioBuffer] = None,
        sample_rate: int = SAMPLE_RATE,
        chunk_size: int = 2048,
        device_index: Optional[int] = None,
    ):
        self.buffer = buffer or CircularAudioBuffer()
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self._stream = None
        self._is_capturing = False
        self._lock = threading.Lock()

    @property
    def is_capturing(self) -> bool:
        """True if physical audio capture stream is actively running."""
        return self._is_capturing

    def _audio_callback(self, indata, frames, time_info, status):
        """Internal callback invoked by sounddevice for each hardware audio chunk."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        samples = indata[:, 0] if indata.ndim > 1 else indata
        self.buffer.write(samples)

    def start_capture(self) -> bool:
        """
        Attempt to start physical audio capture using sounddevice.
        Returns True if hardware capture initialized, False if hardware unavailable.
        """
        try:
            import sounddevice as sd

            devices = sd.query_devices()
            if not devices:
                logger.warning("No audio input devices found.")
                return False

            self._stream = sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._is_capturing = True
            logger.info("Hardware audio capture started successfully.")
            return True
        except Exception as e:
            logger.warning(f"Physical audio capture unavailable ({e}). Operating in simulation/adapter mode.")
            self._is_capturing = False
            return False

    def stop_capture(self) -> None:
        """Stop physical audio stream if active."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._is_capturing = False

    def push_external_chunk(self, samples: np.ndarray) -> None:
        """
        Feed external PCM samples directly into the pipeline (used by scenario replay or WAV feeds).
        """
        self.buffer.write(samples)

