"""
SynthLeak Acoustic Dual-Sensor Cross-Correlation & TDoA Localization.
Computes Time Difference of Arrival (TDoA) between two synchronized sensor streams
and estimates leak distance along the pipeline chainage.

Formula:
  d_leak = (L - (v * delta_t)) / 2
Where:
  L = Distance between Sensor 1 and Sensor 2 (meters)
  v = Acoustic wave propagation velocity in water / pipe wall (~1482 m/s in water)
  delta_t = Time delay calculated from cross-correlation peak (seconds)
"""

import numpy as np
from typing import Tuple, Optional
from shared.constants import SAMPLE_RATE
from backend.config import settings


class AcousticLocalizer:
    """Estimates acoustic leak incident locations between dual sensor pairs using TDoA."""

    def __init__(
        self,
        sr: int = SAMPLE_RATE,
        propagation_speed_mps: float = settings.SPEED_OF_SOUND_WATER_MS,
    ):
        self.sr = sr
        self.propagation_speed = propagation_speed_mps

    def compute_tdoa(
        self,
        signal_s1: np.ndarray,
        signal_s2: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Compute Time Difference of Arrival (TDoA) via cross-correlation.
        Returns:
          (delta_t_seconds, correlation_peak_normalized)
        """
        if len(signal_s1) == 0 or len(signal_s2) == 0:
            return 0.0, 0.0

        # Ensure equal lengths
        min_len = min(len(signal_s1), len(signal_s2))
        s1 = signal_s1[:min_len] - np.mean(signal_s1[:min_len])
        s2 = signal_s2[:min_len] - np.mean(signal_s2[:min_len])

        norm_s1 = np.linalg.norm(s1)
        norm_s2 = np.linalg.norm(s2)

        if norm_s1 < 1e-6 or norm_s2 < 1e-6:
            return 0.0, 0.0

        # Full cross-correlation: np.correlate(s1, s2) shifts s2 relative to s1
        corr = np.correlate(s1, s2, mode="full")
        corr_norm = corr / (norm_s1 * norm_s2)

        peak_idx = int(np.argmax(corr_norm))
        # Center index corresponds to delta_t = 0
        # If s2 is delayed relative to s1 (s2 arrived later), the peak occurs at lag = delay
        lag_samples = (min_len - 1) - peak_idx
        delta_t = float(lag_samples / self.sr)
        peak_score = float(corr_norm[peak_idx])

        return delta_t, peak_score

    def estimate_leak_position(
        self,
        signal_s1: np.ndarray,
        signal_s2: np.ndarray,
        sensor1_chainage: float,
        sensor2_chainage: float,
    ) -> Tuple[Optional[float], float, float]:
        """
        Estimate absolute chainage position of the acoustic anomaly along the pipe.
        Returns:
          (estimated_chainage_meters, delta_t_seconds, confidence)
        """
        distance_between_sensors = abs(sensor2_chainage - sensor1_chainage)
        if distance_between_sensors <= 0:
            return None, 0.0, 0.0

        delta_t, peak_score = self.compute_tdoa(signal_s1, signal_s2)

        # Maximum possible physical acoustic travel time between the sensors
        max_possible_delay = distance_between_sensors / self.propagation_speed
        if abs(delta_t) > max_possible_delay * 1.2:
            # Physically inconsistent delay (likely uncorrelated ambient noise)
            return None, delta_t, peak_score

        # Clamp delay within physical boundary for geometric estimation
        clamped_delta_t = np.clip(delta_t, -max_possible_delay, max_possible_delay)

        # Distance from Sensor 1: d1 = (L - (v * delta_t)) / 2
        d1 = (distance_between_sensors - (self.propagation_speed * clamped_delta_t)) / 2.0

        # Absolute chainage along the pipeline
        estimated_chainage = sensor1_chainage + d1
        return float(round(estimated_chainage, 2)), float(round(delta_t, 5)), float(round(peak_score, 3))
