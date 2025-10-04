# Pipecat Voice Backend Dockerfile
FROM python:3.11-slim as base

# Install system dependencies for audio processing and Pipecat
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    portaudio19-dev \
    libsndfile1-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Silero VAD model at build time (recommended by Pipecat docs)
RUN python -c "import torch; torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True)"

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash pipecat

# Change ownership
RUN chown -R pipecat:pipecat /app

# Switch to non-root user
USER pipecat

# Expose ports (8765 for WebSocket, 8000 for HTTP)
EXPOSE 8765 8000

# Health check for Pipecat service
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PIPECAT_LOG_LEVEL=INFO

# Default command - use the working Pipecat bot
CMD ["python", "bot.py"]
