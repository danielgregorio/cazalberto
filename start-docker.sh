#!/usr/bin/env bash
# Inicia o Cazalberto com Docker.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker não está instalado."
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "❌ Docker Compose não está instalado."
    exit 1
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Criei o arquivo .env. Edite-o, coloque seu DISCORD_TOKEN e rode de novo."
    exit 1
fi

if ! grep -Eq '^DISCORD_TOKEN=.+' .env; then
    echo "❌ DISCORD_TOKEN está vazio no .env."
    exit 1
fi

mkdir -p data audio_clips wow-music

echo "🚀 Iniciando Cazalberto..."
$COMPOSE up -d --build

echo "✅ Cazalberto iniciado!"
echo "  Logs:      $COMPOSE logs -f"
echo "  Parar:     $COMPOSE down"
echo "  Reiniciar: $COMPOSE restart"
echo "Use !sync no Discord (como administrador) para registrar os comandos slash."
