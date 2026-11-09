# SynthLeak Backend & Audio Service Dockerfile
FROM python:3.11-slim as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    DATABASE_PATH=/app/data/synthleak.db

WORKDIR /app

# Install system dependencies for audio processing and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    libportaudio2 \
    portaudio19-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy application directories
COPY shared/ /app/shared/
COPY audio-engine/ /app/audio-engine/
COPY ml/ /app/ml/
COPY backend/ /app/backend/

# Create persistent storage mount directory for SQLite database
RUN mkdir -p /app/data

# Expose backend REST & WebSocket port
EXPOSE 8000

# Container healthcheck (ensures proper JSON array syntax for CMD)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 CMD ["curl","-f","http://localhost:8000/health"]


# Default command launches FastAPI via Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
