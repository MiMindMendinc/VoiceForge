# CPU image for VoiceForge. The model is NOT included: mount it at /app/models,
# e.g. docker run -v "$PWD/models:/app/models" -p 8000:8000 voiceforge
# Set VOICEFORGE_NO_DOWNLOAD=0 to let the container download missing files into that mount.
# Debian's ffmpeg package is built with libmp3lame and libopus (MP3/Opus output).
# WAV stays the default response_format and needs no FFmpeg.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VOICEFORGE_HOST=0.0.0.0 \
    VOICEFORGE_PORT=8000 \
    VOICEFORGE_MODEL_DIR=/app/models \
    VOICEFORGE_NO_DOWNLOAD=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -hide_banner -encoders | grep -q libmp3lame \
    && ffmpeg -hide_banner -encoders | grep -q libopus

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
RUN pip install --no-deps -e . \
    && useradd --create-home --uid 10001 voiceforge \
    && mkdir -p /app/models && chown voiceforge /app/models
USER voiceforge

EXPOSE 8000
CMD ["voiceforge", "serve"]
