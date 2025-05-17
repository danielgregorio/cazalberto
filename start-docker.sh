#!/bin/bash
# Script para iniciar Cazalberto em Docker

# Verifica se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verifica se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "⚠️ Arquivo .env não encontrado. Criando..."
    echo "DISCORD_TOKEN=" > .env
    echo "✅ Arquivo .env criado. Por favor, edite-o e adicione seu token do Discord."
    exit 1
fi

# Verifica se o token está configurado
if grep -q "DISCORD_TOKEN=$" .env; then
    echo "❌ Token do Discord não configurado no arquivo .env"
    echo "Por favor, edite o arquivo .env e adicione seu token: DISCORD_TOKEN=seu_token_aqui"
    exit 1
fi

# Cria diretórios necessários
mkdir -p audio_clips
mkdir -p wow-music/legion
mkdir -p wow-music/classic
mkdir -p wow-music/wotlk

# Verifica se commands.json e playlists.json existem, e cria se não existirem
if [ ! -f commands.json ]; then
    echo "{}" > commands.json
    echo "✅ Arquivo commands.json criado."
fi

if [ ! -f playlists.json ]; then
    echo "{\"playlists\":[]}" > playlists.json
    echo "✅ Arquivo playlists.json criado."
fi

# Inicia o container
echo "🚀 Iniciando Cazalberto..."
docker-compose up -d

# Verifica se iniciou com sucesso
if [ $? -eq 0 ]; then
    echo "✅ Cazalberto iniciado com sucesso!"
    echo ""
    echo "📋 Comandos úteis:"
    echo "  - Ver logs: docker-compose logs -f"
    echo "  - Parar bot: docker-compose down"
    echo "  - Reiniciar: docker-compose restart"
    echo ""
    echo "🎮 Use !sync no Discord para sincronizar os comandos slash."
else
    echo "❌ Erro ao iniciar Cazalberto. Verifique os logs: docker-compose logs"
fi
