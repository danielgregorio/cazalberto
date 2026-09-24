# Cazalberto com Docker

## Jeito rápido

- Linux/macOS: `./start-docker.sh`
- Windows: dê dois cliques em `start-docker.bat`

Na primeira vez, o script cria o `.env` a partir do `.env.example`. Coloque o `DISCORD_TOKEN` nele e rode de novo.

## Manualmente

```bash
cp .env.example .env    # e preencha o DISCORD_TOKEN
docker compose up -d --build
docker compose logs -f
```

## Pastas (volumes)

| No seu computador | No container | Conteúdo |
|---|---|---|
| `./data` | `/app/data` | `commands.json`, `playlists.json` |
| `./audio_clips` | `/app/audio_clips` | áudios aprendidos |
| `WOW_OST_HOST_DIR` (padrão `./wow-music`) | `/app/wow-ost` (só leitura) | trilhas do WoW |

Para usar as trilhas do WoW que já estão no seu computador, coloque no `.env`, por exemplo:

```
WOW_OST_HOST_DIR=D:/music/wow-ost
```

O container roda com o usuário de UID 1000. No Linux, se o bot não conseguir gravar em `data/` ou
`audio_clips/`, ajuste o dono das pastas: `sudo chown -R 1000:1000 data audio_clips`.

## Comandos úteis

```bash
docker compose restart                                   # reiniciar
docker compose down                                      # parar
git pull && docker compose up -d --build                 # atualizar
docker compose run --rm cazalberto python -m cazalberto --sync   # registrar comandos slash
```

## Problemas comuns

- **O bot não inicia**: veja `docker compose logs`. Geralmente é o `DISCORD_TOKEN` errado ou vazio.
- **Os comandos slash não aparecem**: rode `!sync` no Discord (como administrador) ou o comando `--sync` acima.
- **`/wow` diz que está desativado**: confira o `WOW_OST_HOST_DIR` no `.env`.
