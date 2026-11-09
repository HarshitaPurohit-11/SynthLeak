"""
SynthLeak Backend Configuration Settings.
Loads parameters from environment variables with sensible production and development defaults.
"""

import os
from pathlib import Path
# Settings dataclass container


class Settings:
    """Application settings and runtime configuration."""
    PROJECT_NAME: str = "SynthLeak"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # API & Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @property
    def CORS_ORIGINS(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "")
        if raw.strip():
            origins = [o.strip() for o in raw.split(",") if o.strip()]
            if origins:
                return origins
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]

    CORS_ORIGIN_REGEX: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"https://.*(netlify\.app|vercel\.app|onrender\.com).*"
    )

    # Database
    DEFAULT_DB: str = str(Path(__file__).resolve().parent.parent / "data" / "synthleak.db")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", DEFAULT_DB)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

    # Audio Engine & DSP
    SAMPLE_RATE: int = 44100
    N_FFT: int = 1024
    HOP_LENGTH: int = 512
    N_MELS: int = 128
    CLIP_SAMPLES: int = 65536
    WS_TARGET_FPS: int = 15

    # Sound Speed in Water (m/s) for TDoA Acoustic Localization
    SPEED_OF_SOUND_WATER_MS: float = 1482.0


settings = Settings()
