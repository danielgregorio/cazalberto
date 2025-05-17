FROM python:3.9-slim

LABEL maintainer="Daniel Gregorio"
LABEL description="Cazalberto Discord Bot - Bot para reprodução de áudios no Discord"

# Instalar ferramentas essenciais e FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório para o app
WORKDIR /app

# Copiar requirements.txt primeiro (para melhor cache do Docker)
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do bot
COPY . .

# Criar diretórios de dados necessários
RUN mkdir -p audio_clips wow-music/legion wow-music/classic wow-music/wotlk

# Token do Discord deve ser passado como variável de ambiente
ENV DISCORD_TOKEN=""

# Volume para persistência de dados
VOLUME ["/app/audio_clips", "/app/wow-music"]

# Comando para iniciar o bot
CMD ["python", "bot.py"]
