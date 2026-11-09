"""
SynthLeak Thread-Safe Circular Audio Buffer & Mel Spectrogram Processor.
Authoritative parameters:
  - SAMPLE_RATE = 44100 Hz
  - N_FFT = 1024
  - HOP_LENGTH = 512
  - N_MELS = 128
  - CLIP_SAMPLES = 65536 (~1.486s, exactly 128 frames * 512 hop)
"""

import threading
import numpy as np
from typing import Optional, Tuple
from shared.constants import (
    SAMPLE_RATE,
    N_FFT,
    HOP_LENGTH,
    N_MELS,
    CLIP_SAMPLES,
    SPECTROGRAM_SHAPE,
)


class CircularAudioBuffer:
    """
    Thread-safe circular ring buffer for continuous real-time audio streams.
    Stores raw float32 PCM samples in chronological sequence with overwrite protection.
    """

    def __init__(self, capacity_samples: int = CLIP_SAMPLES * 2):
        self.capacity = capacity_samples
        self.buffer = np.zeros(self.capacity, dtype=np.float32)
        self.write_index = 0
        self.total_samples_written = 0
        self.lock = threading.Lock()

    def write(self, samples: np.ndarray) -> None:
        """
        Append incoming PCM audio samples into the circular buffer.
        Handles wrapping and thread-safe pointer increments.
        """
        if not isinstance(samples, np.ndarray):
            samples = np.asarray(samples, dtype=np.float32)

        if samples.ndim > 1:
            samples = samples.flatten()

        samples = samples.astype(np.float32)
        num_samples = len(samples)
        if num_samples == 0:
            return

        with self.lock:
            if num_samples >= self.capacity:
                # Samples exceed capacity; retain only the most recent chunk
                self.buffer[:] = samples[-self.capacity:]
                self.write_index = 0
                self.total_samples_written += num_samples
                return

            end_index = self.write_index + num_samples
            if end_index <= self.capacity:
                self.buffer[self.write_index:end_index] = samples
            else:
                first_part = self.capacity - self.write_index
                second_part = num_samples - first_part
                self.buffer[self.write_index:self.capacity] = samples[:first_part]
                self.buffer[0:second_part] = samples[first_part:]

            self.write_index = (self.write_index + num_samples) % self.capacity
            self.total_samples_written += num_samples

    def get_latest(self, num_samples: int = CLIP_SAMPLES) -> np.ndarray:
        """
        Extract the most recent `num_samples` in strict chronological order.
        If buffer has fewer samples than requested, zero-pads the beginning.
        """
        with self.lock:
            available = min(self.total_samples_written, self.capacity)
            if available == 0:
                return np.zeros(num_samples, dtype=np.float32)

            fetch_count = min(num_samples, available)
            result = np.zeros(num_samples, dtype=np.float32)

            start_idx = (self.write_index - fetch_count) % self.capacity
            if start_idx + fetch_count <= self.capacity:
                ordered = self.buffer[start_idx:start_idx + fetch_count]
            else:
                part1 = self.capacity - start_idx
                part2 = fetch_count - part1
                ordered = np.concatenate([self.buffer[start_idx:], self.buffer[:part2]])

            # Place at tail of result array (chronological padding)
            result[-fetch_count:] = ordered
            return result

    def clear(self) -> None:
        """Reset the buffer state."""
        with self.lock:
            self.buffer.fill(0)
            self.write_index = 0
            self.total_samples_written = 0


# Pre-compute Mel filterbank weights once to ensure high-performance DSP
def _create_mel_filterbank(sr: int, n_fft: int, n_mels: int) -> np.ndarray:
    """Construct standard triangular Mel scale filterbank matrix."""
    f_min = 0.0
    f_max = sr / 2.0

    def hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel):
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    mel_min = hz_to_mel(f_min)
    mel_max = hz_to_mel(f_max)
    mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_points = mel_to_hz(mel_points)

    bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)
    num_bins = n_fft // 2 + 1
    filterbank = np.zeros((n_mels, num_bins), dtype=np.float32)

    for m in range(1, n_mels + 1):
        left = bin_points[m - 1]
        center = bin_points[m]
        right = bin_points[m + 1]

        if center > left:
            filterbank[m - 1, left:center] = (np.arange(left, center) - left) / (center - left)
        if right > center:
            filterbank[m - 1, center:right] = (right - np.arange(center, right)) / (right - center)

    return filterbank


MEL_FILTERBANK = _create_mel_filterbank(SAMPLE_RATE, N_FFT, N_MELS)


class AudioProcessor:
    """
    Computes Short-Time Fourier Transform (STFT), Mel bin energies,
    instantaneous RMS dBFS levels, and spectral peaks.
    """

    @staticmethod
    def compute_sound_level_db(samples: np.ndarray) -> float:
        """Compute instantaneous Root Mean Square (RMS) sound level in dBFS."""
        if len(samples) == 0:
            return -100.0
        rms = np.sqrt(np.mean(samples ** 2))
        if rms <= 1e-9:
            return -100.0
        return float(np.clip(20.0 * np.log10(rms), -100.0, 0.0))

    @staticmethod
    def compute_mel_spectrogram(samples: np.ndarray) -> np.ndarray:
        """
        Compute continuous STFT Mel spectrogram tensor of shape (N_MELS, N_FRAMES).
        Normalized to [0.0, 1.0].
        """
        if len(samples) < N_FFT:
            samples = np.pad(samples, (0, N_FFT - len(samples)))

        window = np.hanning(N_FFT).astype(np.float32)
        num_frames = (len(samples) - N_FFT) // HOP_LENGTH + 1
        num_bins = N_FFT // 2 + 1

        power_spec = np.zeros((num_bins, num_frames), dtype=np.float32)
        for i in range(num_frames):
            start = i * HOP_LENGTH
            frame = samples[start:start + N_FFT] * window
            fft_result = np.fft.rfft(frame, n=N_FFT)
            power_spec[:, i] = np.abs(fft_result) ** 2

        # Apply Mel Filterbank: (n_mels, num_bins) @ (num_bins, num_frames) -> (n_mels, num_frames)
        mel_spec = np.dot(MEL_FILTERBANK, power_spec)

        # Log power scale with dynamic range normalization
        mel_log = np.log10(np.maximum(mel_spec, 1e-6))
        min_val = mel_log.min()
        max_val = mel_log.max()
        if max_val > min_val:
            mel_normalized = (mel_log - min_val) / (max_val - min_val)
        else:
            mel_normalized = np.zeros_like(mel_log)

        return mel_normalized.astype(np.float32)

    @staticmethod
    def compute_single_mel_frame(samples: np.ndarray) -> list[float]:
        """
        Extract the latest single Mel spectrum frame (128 bins) for WebSocket telemetry.
        Guaranteed to return exactly N_MELS floats in [0.0, 1.0].
        """
        if len(samples) < N_FFT:
            frame = np.pad(samples, (0, N_FFT - len(samples)))
        else:
            frame = samples[-N_FFT:]

        window = np.hanning(N_FFT).astype(np.float32)
        fft_mag = np.abs(np.fft.rfft(frame * window, n=N_FFT)) ** 2
        mel_frame = np.dot(MEL_FILTERBANK, fft_mag)

        mel_log = np.log10(np.maximum(mel_frame, 1e-6))
        min_val = mel_log.min()
        max_val = mel_log.max()
        if max_val > min_val:
            normalized = (mel_log - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros(N_MELS, dtype=np.float32)

        return [round(float(v), 4) for v in normalized[:N_MELS]]

    @staticmethod
    def compute_dominant_frequency(samples: np.ndarray, sr: int = SAMPLE_RATE) -> float:
        """Find the dominant spectral peak frequency in Hz."""
        if len(samples) < N_FFT:
            return 0.0
        frame = samples[-N_FFT:]
        fft_mag = np.abs(np.fft.rfft(frame))
        freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
        peak_idx = int(np.argmax(fft_mag))
        return float(round(freqs[peak_idx], 1))

