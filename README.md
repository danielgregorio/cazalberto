# Cazalberto 🤖🎵

Bot de Discord para tocar clipes de áudio, montar playlists e ouvir as trilhas sonoras de World of Warcraft.

## Comandos

| Comando | O que faz |
|---|---|
| `/tocar <comando>` | Toca um áudio salvo ou uma música do WoW (tem autocompletar) |
| `/aprendido` | Lista os áudios com botões para tocar |
| `/aprender <comando> <url>` | Ensina um áudio novo a partir de um link |
| `/esquecer <comando>` | Remove um áudio (e tira das playlists) |
| `/parar` | Para o que está tocando |
| `/sair` | Sai do canal de voz |
| `/wow <expansão>` | Lista as músicas de uma expansão do WoW (`classic`, `wotlk`, `2`, `kara`...) |
| `/criar_playlist`, `/adicionar_playlist`, `/remover_playlist` | Monta playlists |
| `/ver_playlist`, `/listar_playlists`, `/excluir_playlist` | Consulta e apaga playlists |
| `/tocar_playlist <playlist> [repetir] [aleatorio]` | Toca uma playlist |
| `/piada`, `/status`, `/ajuda` | Diversos |

Comandos de administrador, com prefixo:

- `!sync`: registra os comandos slash no Discord (pode levar até 1h para aparecer em todos os servidores).
- `!sync aqui`: registra só no servidor atual (aparece na hora).
- `!recarregar`: relê `commands.json`, playlists e a pasta do WoW sem reiniciar.

## Rodando

Pré-requisitos: Python 3.10+ e [FFmpeg](https://ffmpeg.org/download.html) no PATH
(Windows: `winget install ffmpeg`; macOS: `brew install ffmpeg`; Debian/Ubuntu: `sudo apt install ffmpeg`).

```bash
git clone https://github.com/danielgregorio/cazalberto.git
cd cazalberto
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# edite o .env e coloque o DISCORD_TOKEN
python -m cazalberto --sync     # registra os comandos slash (só precisa quando eles mudam)
python -m cazalberto            # inicia o bot (python bot.py também funciona)
```

Com Docker, veja [DOCKER.md](DOCKER.md).

## Configuração

Tudo é configurado por variáveis de ambiente ou pelo arquivo `.env` (modelo em [.env.example](.env.example)):

| Variável | Padrão | Descrição |
|---|---|---|
| `DISCORD_TOKEN` | (obrigatória) | Token do bot |
| `WOW_OST_DIR` | `wow-music/` se existir | Pasta com as trilhas do WoW; vazio desativa |
| `DATA_DIR` | `data` | Onde ficam `commands.json` e `playlists.json` |
| `AUDIO_DIR` | `audio_clips` | Onde ficam os áudios aprendidos |
| `SYNC_ON_STARTUP` | `false` | Registrar os comandos slash sempre que iniciar |
| `DEV_GUILD_ID` | (vazio) | Servidor de testes: o sync vale só nele e aparece na hora |
| `COMMAND_PREFIX` | `!` | Prefixo dos comandos de administrador |
| `LOG_LEVEL` / `LOG_FILE` | `INFO` / `bot.log` | Logs (o arquivo gira a cada 5 MB) |
| `MAX_DOWNLOAD_MB` | `10` | Tamanho máximo de um áudio no `/aprender` |

### Trilhas do WoW

As músicas são encontradas lendo a pasta `WOW_OST_DIR`. As subpastas são reconhecidas pela versão no começo do nome:

```
wow-ost/
├── 1.0 Classic/1. Legends of Azeroth.mp3      -> classic-legends-of-azeroth
├── 7.1 Return to Karazhan/1. Karazhan.mp3     -> kara-karazhan
└── 11.1 Undermine(D)/9. The Gallagio.mp3      -> undermine-the-gallagio
```

Também dá para usar pastas com o prefixo como nome (`wow-music/classic/`, `wow-music/wotlk/`...).
No `/tocar` basta um pedaço do nome: `/tocar classic-elwynn` encontra `classic-forest-elwynn-forest`.

## Estrutura

```
cazalberto/
├── __main__.py        # ponto de entrada (python -m cazalberto)
├── bot.py             # CazalbertoBot: carrega serviços e cogs, trata erros
├── config.py          # Settings, lidas do ambiente/.env
├── storage.py         # leitura/escrita de JSON (escrita atômica)
├── playlists.py       # PlaylistStore
├── audio/
│   ├── library.py     # áudios aprendidos (commands.json)
│   ├── wow.py         # catálogo das trilhas do WoW
│   ├── player.py      # conexão de voz, reprodução e filas
│   └── download.py    # download com limite de tamanho
├── cogs/              # comandos: audio, wow, playlists, misc, admin
└── ui/browser.py      # lista paginada com botões
data/                  # commands.json, playlists.json (e jokes.json opcional)
tests/                 # testes (pytest)
```

## Desenvolvimento

```bash
pip install -r requirements-dev.txt
pytest            # testes
ruff check .      # lint
ruff format .     # formatação
```

A CI (GitHub Actions) roda lint, testes e o build do Docker em todo push e pull request.
Veja também [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

MIT. Veja [LICENSE](LICENSE).

Desenvolvido por Daniel Gregorio.
