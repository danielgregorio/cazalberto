# Dockerização do Cazalberto

Este documento detalha como executar o Cazalberto usando Docker.

## Pré-requisitos

- Docker instalado
- Docker Compose instalado
- Token do bot Discord

## Configuração

1. Crie um arquivo `.env` na raiz do projeto com o token do seu bot:

```
DISCORD_TOKEN=seu_token_aqui
```

2. Verifique se as pastas necessárias existem:
   - `audio_clips` (para áudios personalizados)
   - `wow-music` (para áudios do WoW)

## Executando com Docker Compose

Para iniciar o bot:

```bash
docker-compose up -d
```

Para visualizar os logs:

```bash
docker-compose logs -f
```

Para parar o bot:

```bash
docker-compose down
```

## Build e execução manual

Se preferir construir e executar manualmente:

1. Construa a imagem:

```bash
docker build -t cazalberto .
```

2. Execute o container:

```bash
docker run -d \
  --name cazalberto-bot \
  -e DISCORD_TOKEN=seu_token_aqui \
  -v ./audio_clips:/app/audio_clips \
  -v ./wow-music:/app/wow-music \
  -v ./commands.json:/app/commands.json \
  -v ./playlists.json:/app/playlists.json \
  cazalberto
```

## Volumes

Os seguintes volumes são usados para persistência:

- `./audio_clips`: Armazena os arquivos de áudio personalizados
- `./wow-music`: Armazena os arquivos de música do WoW
- `./commands.json`: Configuração dos comandos
- `./playlists.json`: Configuração das playlists

## Comandos úteis

### Reiniciar o bot

```bash
docker-compose restart
```

### Atualizar para uma nova versão

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Executar o comando de sincronização

```bash
docker exec -it cazalberto-bot python -c "from discord.ext import commands; bot = commands.Bot(command_prefix='!'); bot.tree.sync()"
```

## Resolução de problemas

Se o bot não iniciar, verifique os logs:

```bash
docker-compose logs
```

Certifique-se de que:

1. O token do Discord está correto
2. Os volumes estão configurados corretamente
3. As permissões dos arquivos são adequadas
