FROM python:3.12-slim

LABEL maintainer="Daniel Gregorio" \
      description="Cazalberto - bot de Discord para tocar clipes de áudio"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data \
    AUDIO_DIR=/app/audio_clips \
    LOG_FILE=

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cazalberto ./cazalberto
COPY bot.py ./

# Roda sem root; os volumes de dados precisam ser graváveis por esse usuário.
RUN useradd --create-home --uid 1000 cazalberto \
    && mkdir -p /app/data /app/audio_clips \
    && chown -R cazalberto:cazalberto /app/data /app/audio_clips
USER cazalberto

VOLUME ["/app/data", "/app/audio_clips"]

CMD ["python", "-m", "cazalberto"]
