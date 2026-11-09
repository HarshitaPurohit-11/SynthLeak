"""SynthLeak DSP package (owned by Acoustic Signal Processing & ML).

NOTE: the parent folder is named ``audio-engine`` (with a hyphen), so it is not
importable as a Python package. Consumers add ``<repo>/audio-engine`` to
``sys.path`` and then ``import dsp``. ``ml/preprocessing.py`` does this for you.
"""

from dsp.filters import (  # noqa: F401
    AdaptiveNoiseSuppressor,
    adaptive_spectral_subtraction,
    bandpass_filter,
)
from dsp.spectrogram import (  # noqa: F401
    dominant_frequency_hz,
    log_mel_spectrogram,
    mel_filterbank,
    mel_frames_normalized,
    mel_spectrogram,
    rms_dbfs,
    stft_magnitude,
)
