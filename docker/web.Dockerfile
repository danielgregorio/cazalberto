# Multi-stage build para otimização
FROM python:3.11-slim as builder

WORKDIR /build

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Configurar Poetry
RUN poetry config virtualenvs.create false

# Exportar requirements
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Instalar dependências
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ===========================================
# Imagem final
# ===========================================
FROM python:3.11-slim

LABEL maintainer="Daniel Gregorio"
LABEL description="Cazalberto Web Panel"

WORKDIR /app

# Instalar runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels do builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Instalar dependências
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copiar código da aplicação
COPY src/ ./src/
COPY .env.example .env.example

# Criar diretórios necessários
RUN mkdir -p /app/data /app/audio_clips /app/logs

# Criar usuário não-root
RUN useradd -m -u 1000 cazalberto && \
    chown -R cazalberto:cazalberto /app

USER cazalberto

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expor porta
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando padrão
CMD ["uvicorn", "cazalberto.web.app:app", "--host", "0.0.0.0", "--port", "8080"]
