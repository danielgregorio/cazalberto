# Docker - Cazalberto v2.0.0

Guia completo para executar o Cazalberto usando Docker.

## Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Token do bot Discord

## Quick Start

```bash
# 1. Configure o token
cp .env.example .env
# Edite .env e adicione seu DISCORD_TOKEN

# 2. Crie os arquivos de dados (se não existirem)
touch commands.json playlists.json favorites.json stats.json bot.log
echo "{}" > commands.json
echo "{}" > playlists.json
echo "{}" > favorites.json
echo "{}" > stats.json

# 3. Inicie o bot
docker-compose up -d
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Obrigatório
DISCORD_TOKEN=seu_token_aqui

# Opcional - Rate Limiting
RATE_LIMIT_COMMANDS=5
RATE_LIMIT_SECONDS=10
```

### Estrutura de Pastas

```
cazalberto/
├── .env                 # Configuração (criar)
├── audio_clips/         # Áudios aprendidos (auto-criado)
├── wow-music/           # Músicas do WoW (opcional)
├── commands.json        # Banco de comandos
├── playlists.json       # Playlists
├── favorites.json       # Favoritos dos usuários
├── stats.json           # Estatísticas de uso
└── bot.log              # Logs
```

## Comandos Docker Compose

### Operações básicas

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs em tempo real
docker-compose logs -f

# Ver status
docker-compose ps
```

### Atualização

```bash
# Baixar nova versão e reconstruir
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Build Manual (sem Compose)

```bash
# Build da imagem
docker build -t cazalberto:2.0.0 .

# Executar
docker run -d \
  --name cazalberto-bot \
  --restart unless-stopped \
  -e DISCORD_TOKEN=seu_token \
  -e WOW_OST_FOLDER=/app/wow-music \
  -v $(pwd)/audio_clips:/app/audio_clips \
  -v $(pwd)/wow-music:/app/wow-music \
  -v $(pwd)/commands.json:/app/commands.json \
  -v $(pwd)/playlists.json:/app/playlists.json \
  -v $(pwd)/favorites.json:/app/favorites.json \
  -v $(pwd)/stats.json:/app/stats.json \
  -v $(pwd)/bot.log:/app/bot.log \
  cazalberto:2.0.0
```

## Volumes e Persistência

| Volume | Descrição |
|--------|-----------|
| `audio_clips/` | Áudios aprendidos pelo bot |
| `wow-music/` | Músicas do World of Warcraft |
| `commands.json` | Mapeamento nome -> arquivo |
| `playlists.json` | Playlists criadas |
| `favorites.json` | Favoritos por usuário |
| `stats.json` | Contagem de reproduções |
| `bot.log` | Logs de execução |

## Recursos e Limites

O docker-compose.yml configura:
- **Memória máxima:** 512MB
- **Memória reservada:** 128MB
- **Logs:** máx 10MB, 3 arquivos

Para ajustar, edite a seção `deploy.resources` no docker-compose.yml.

## Troubleshooting

### Bot não inicia

```bash
# Verificar logs
docker-compose logs

# Verificar se o container está rodando
docker-compose ps
```

### Erro de permissão nos volumes

```bash
# Linux/Mac: ajustar permissões
sudo chown -R 1000:1000 audio_clips wow-music
chmod 666 commands.json playlists.json favorites.json stats.json bot.log
```

### Token inválido

1. Verifique se o `.env` existe e contém `DISCORD_TOKEN`
2. Confirme que o token está correto no Discord Developer Portal
3. Recrie o container: `docker-compose up -d --force-recreate`

### Áudio não funciona

- FFmpeg já está incluído na imagem Docker
- Verifique se os arquivos de áudio existem nos volumes montados

## Healthcheck

O container inclui healthcheck automático:
- Intervalo: 30 segundos
- Timeout: 10 segundos
- Retries: 3

Para verificar:
```bash
docker inspect cazalberto-bot --format='{{.State.Health.Status}}'
```
