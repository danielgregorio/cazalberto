FROM python:3.9-slim

LABEL maintainer="Daniel Gregorio"
LABEL description="Cazalberto Discord Bot v2.0.0"
LABEL version="2.0.0"

# Instalar FFmpeg e dependências
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 botuser

# Criar diretório para o app
WORKDIR /app

# Copiar requirements.txt primeiro (para melhor cache)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do bot
COPY --chown=botuser:botuser . .

# Criar diretórios de dados
RUN mkdir -p audio_clips wow-music data \
    && chown -R botuser:botuser /app

# Mudar para usuário não-root
USER botuser

# Variáveis de ambiente
ENV DISCORD_TOKEN=""
ENV WOW_OST_FOLDER="/app/wow-music"
ENV RATE_LIMIT_COMMANDS="5"
ENV RATE_LIMIT_SECONDS="10"
ENV PYTHONUNBUFFERED=1

# Volumes para persistência
VOLUME ["/app/audio_clips", "/app/wow-music", "/app/data"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('bot.log') else 1)"

# Comando para iniciar
CMD ["python", "bot.py"]
