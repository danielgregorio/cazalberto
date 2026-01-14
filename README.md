# Cazalberto Discord Bot

## Descrição
Cazalberto é um bot de Discord para reprodução de áudio com suporte a clipes personalizados, músicas do World of Warcraft, playlists e sistema de favoritos.

## Funcionalidades

### Reprodução de Áudio
- Tocar áudios personalizados e músicas do WoW
- Sistema de fila de reprodução
- Controle de volume (0-200%)
- Loop de música
- Pausar/continuar/pular

### Gerenciamento
- Aprender novos áudios via URL
- Busca com sugestões fuzzy
- Sistema de favoritos por usuário
- Ranking dos mais tocados

### Playlists
- Criar e gerenciar playlists
- Reprodução sequencial ou aleatória
- Repetição configurável

### WoW OST
- Suporte a todas as expansões (Classic até Undermine)
- Interface interativa com botões

## Pré-requisitos
- Python 3.9+
- FFmpeg instalado no sistema

## Instalação do FFmpeg

### Windows
1. Baixe o FFmpeg de: https://github.com/BtbN/FFmpeg-Builds/releases
2. Baixe a versão "ffmpeg-master-latest-win64-gpl.zip"
3. Extraia e adicione a pasta `bin` ao PATH do sistema

### macOS (usando Homebrew)
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install ffmpeg
```

## Configuração do Projeto

1. Clone o repositório
```bash
git clone https://github.com/danielgregorio/cazalberto.git
cd cazalberto
```

2. Crie um ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências
```bash
pip install -r requirements.txt
```

4. Configuração (copie o exemplo e edite)
```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```env
# Token do Discord (obrigatório)
DISCORD_TOKEN=seu_token_aqui

# Pasta de músicas do WoW (opcional)
WOW_OST_FOLDER=/caminho/para/wow-ost

# Rate limiting (opcional)
RATE_LIMIT_COMMANDS=5
RATE_LIMIT_SECONDS=10
```

## Executando o Bot

### Diretamente
```bash
python bot.py
```

### Com Docker
```bash
docker-compose up -d
```

## Comandos Disponíveis

### Reprodução
| Comando | Descrição |
|---------|-----------|
| `/tocar <nome>` | Toca um áudio |
| `/fila <nome>` | Adiciona à fila |
| `/ver_fila` | Mostra a fila atual |
| `/limpar_fila` | Limpa a fila |
| `/pausar` | Pausa a reprodução |
| `/continuar` | Continua a reprodução |
| `/pular` | Pula para o próximo |
| `/volume <0-200>` | Ajusta o volume |
| `/loop` | Ativa/desativa loop |
| `/sair` | Sai do canal de voz |

### Gerenciamento de Áudio
| Comando | Descrição |
|---------|-----------|
| `/aprender <nome> <url>` | Adiciona novo áudio |
| `/esquecer <nome>` | Remove um áudio |
| `/aprendido` | Lista todos os áudios |
| `/buscar <termo>` | Busca áudios |
| `/wow <expansão>` | Lista áudios do WoW |

### Favoritos
| Comando | Descrição |
|---------|-----------|
| `/favoritar <nome>` | Favorita um áudio |
| `/desfavoritar <nome>` | Remove dos favoritos |
| `/favoritos` | Mostra seus favoritos |

### Playlists
| Comando | Descrição |
|---------|-----------|
| `/criar_playlist <nome>` | Cria uma playlist |
| `/adicionar_playlist <playlist> <audio>` | Adiciona áudio |
| `/remover_playlist <playlist> <audio>` | Remove áudio |
| `/ver_playlist <playlist>` | Mostra conteúdo |
| `/listar_playlists` | Lista playlists |
| `/excluir_playlist <playlist>` | Exclui playlist |
| `/tocar_playlist <playlist>` | Toca playlist |
| `/parar_playlist` | Para a playlist |

### Outros
| Comando | Descrição |
|---------|-----------|
| `/ranking` | Ranking dos mais tocados |
| `/piada` | Conta uma piada |
| `/status` | Status do bot |
| `/ajuda` | Lista de comandos |

## Expansões do WoW Suportadas

| Número | Nome | Aliases |
|--------|------|---------|
| 0 | Classic | classic, vanilla |
| 1 | The Burning Crusade | tbc, burning |
| 2 | Wrath of the Lich King | wotlk, wrath |
| 3 | Cataclysm | cata |
| 4 | Mists of Pandaria | mop, pandaria |
| 5 | Warlords of Draenor | wod, draenor |
| 6 | Legion | legion |
| 7 | Battle for Azeroth | bfa |
| 8 | Shadowlands | sl |
| 9 | Dragonflight | df |
| 10 | The War Within | tww |
| 11 | Undermine | undermine |

Exemplo: `/tocar wotlk-dalaran` ou `/wow 2`

## Solução de Problemas
- Certifique-se de que o FFmpeg está instalado e no PATH
- Verifique o arquivo `bot.log` para detalhes de erros
- Confirme que todas as dependências estão instaladas
- Para WoW: configure WOW_OST_FOLDER no .env ou crie pasta `wow-music`

## Contribuição
1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## Licença
MIT License (veja LICENSE para detalhes)

## Créditos
Desenvolvido por Daniel Gregorio
