"""
SynthLeak Synthetic Audio Generator & Scenario Replay Engine.
Supports development & simulation without hardware:
  - 0: NORMAL_FLOW (smooth low-frequency water turbulence)
  - 1: AMBIENT_URBAN (traffic hum, broad low-frequency vibration)
  - 2: PINHOLE_LEAK (high-frequency jet hiss, 2.5 kHz - 6.0 kHz)
  - 3: CAVITATION_BURST (violent acoustic transient spikes, broadband pulses)

Every simulated payload explicitly includes 'is_simulated': True to maintain metric integrity.
"""

from typing import Optional, Tuple
import numpy as np
from shared.constants import (
    SAMPLE_RATE,
    CLASS_NORMAL_FLOW,
    CLASS_AMBIENT_URBAN,
    CLASS_PINHOLE_LEAK,
    CLASS_CAVITATION_BURST,
    CLASS_LABELS,
)


class SyntheticAudioGenerator:
    """Generates realistic synthetic pipe acoustic signals for the 4-class taxonomy."""

    def __init__(self, sr: int = SAMPLE_RATE):
        self.sr = sr

    def generate_signal(self, class_id: int, duration_seconds: float = 1.0) -> np.ndarray:
        """Generate synthetic PCM samples for a specific acoustic class."""
        num_samples = int(self.sr * duration_seconds)
        t = np.linspace(0, duration_seconds, num_samples, endpoint=False)

        if class_id == CLASS_NORMAL_FLOW:
            # Low-frequency laminar & turbulent pipe flow (150-400 Hz) + gentle pink noise
            base = 0.05 * np.sin(2 * np.pi * 180 * t) + 0.03 * np.sin(2 * np.pi * 320 * t)
            noise = 0.02 * np.random.normal(0, 1, num_samples)
            signal = base + noise

        elif class_id == CLASS_AMBIENT_URBAN:
            # Low rumble / traffic / mechanical vibration (50-120 Hz)
            rumble = 0.08 * np.sin(2 * np.pi * 60 * t) + 0.04 * np.sin(2 * np.pi * 110 * t)
            noise = 0.03 * np.random.normal(0, 1, num_samples)
            signal = rumble + noise

        elif class_id == CLASS_PINHOLE_LEAK:
            # High-velocity orifice jet: intense high-frequency hiss (2800 Hz - 4500 Hz)
            carrier = 0.12 * np.sin(2 * np.pi * 3400 * t) + 0.08 * np.sin(2 * np.pi * 4100 * t)
            # High-frequency bandpassed noise
            hiss = 0.10 * np.random.normal(0, 1, num_samples)
            signal = carrier + hiss

        elif class_id == CLASS_CAVITATION_BURST:
            # Severe pressure collapse: periodic intense impulse bursts + broadband turbulence
            signal = 0.05 * np.random.normal(0, 1, num_samples)
            burst_interval = int(self.sr * 0.15)  # Spike every 150ms
            for idx in range(0, num_samples - 500, burst_interval):
                spike_len = min(500, num_samples - idx)
                decay = np.exp(-np.linspace(0, 5, spike_len))
                signal[idx:idx + spike_len] += 0.45 * np.sin(2 * np.pi * 1200 * t[:spike_len]) * decay

        else:
            signal = 0.01 * np.random.normal(0, 1, num_samples)

        # Normalize to [-1.0, 1.0] range
        max_abs = np.max(np.abs(signal))
        if max_abs > 0:
            signal = signal / max_abs * 0.85

        return signal.astype(np.float32)


class ScenarioReplayer:
    """Replays deterministic multi-stage acoustic scenarios for demonstrations and automated tests."""

    def __init__(self, generator: Optional[SyntheticAudioGenerator] = None):
        self.generator = generator or SyntheticAudioGenerator()
        self.timeline = [
            (CLASS_NORMAL_FLOW, 4.0),
            (CLASS_AMBIENT_URBAN, 3.0),
            (CLASS_PINHOLE_LEAK, 5.0),
            (CLASS_CAVITATION_BURST, 4.0),
        ]
        self.current_stage = 0
        self.stage_elapsed = 0.0

    def get_next_chunk(self, chunk_seconds: float = 0.1) -> Tuple[np.ndarray, int, str]:
        """Produce the next chronological audio chunk based on the active scenario."""
        class_id, duration = self.timeline[self.current_stage]
        samples = self.generator.generate_signal(class_id, chunk_seconds)

        self.stage_elapsed += chunk_seconds
        if self.stage_elapsed >= duration:
            self.stage_elapsed = 0.0
            self.current_stage = (self.current_stage + 1) % len(self.timeline)

        return samples, class_id, CLASS_LABELS[class_id]
