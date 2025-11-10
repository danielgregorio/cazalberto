# 🤖 Cazalberto Bot v2.0

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Poetry](https://img.shields.io/badge/Poetry-1.7+-blue.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Bot Discord moderno para reprodução de áudio com painel de controle web integrado.

[Funcionalidades](#-funcionalidades) •
[Instalação](#-instalação-rápida) •
[Uso](#-uso) •
[API](#-api-rest) •
[Desenvolvimento](#-desenvolvimento)

</div>

---

## ✨ Funcionalidades

### 🎵 Bot Discord
- ✅ Reprodução de clipes de áudio personalizados
- ✅ Sistema de playlists com repeat/shuffle
- ✅ Integração completa com trilhas sonoras do World of Warcraft (12 expansões)
- ✅ UI interativa com botões e paginação
- ✅ Sugestões inteligentes de comandos (fuzzy matching)
- ✅ Sistema de cache para performance
- ✅ Suporte multi-servidor

### 🌐 Painel Web
- ✅ Dashboard com estatísticas
- ✅ Gerenciamento de áudios (CRUD completo)
- ✅ Gerenciamento de playlists
- ✅ API REST documentada
- ✅ Interface moderna e responsiva
- ✅ Upload de arquivos de áudio

### 🛠️ Infraestrutura
- ✅ Banco de dados SQLite com SQLAlchemy 2.0 (async)
- ✅ Configuração via variáveis de ambiente (Pydantic Settings)
- ✅ Type hints completos (mypy strict)
- ✅ Testes automatizados (pytest + coverage)
- ✅ CI/CD com GitHub Actions
- ✅ Docker multi-container
- ✅ Code quality (Black, Ruff, isort)
- ✅ Pre-commit hooks

---

## 🚀 Instalação Rápida

### Método 1: Docker (Recomendado)

```bash
# 1. Clonar repositório
git clone https://github.com/danielgregorio/cazalberto.git
cd cazalberto

# 2. Configurar ambiente
cp .env.example .env
nano .env  # Adicionar DISCORD_TOKEN

# 3. Iniciar com Docker
docker-compose -f docker-compose.new.yml up -d

# 4. Acessar painel web
open http://localhost:8080
```

### Método 2: Local (Desenvolvimento)

```bash
# 1. Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 2. Clonar e instalar
git clone https://github.com/danielgregorio/cazalberto.git
cd cazalberto
poetry install

# 3. Configurar
cp .env.example .env
nano .env

# 4. Migrar dados (se vindo da v1.x)
poetry run python -m src.cazalberto.scripts.init_db
poetry run python -m src.cazalberto.scripts.migrate_json_to_db

# 5. Executar
poetry run python -m src.cazalberto.bot          # Bot
poetry run python -m src.cazalberto.web.app      # Web (em outro terminal)
```

---

## 📖 Uso

### Comandos do Bot

#### Áudio Básico
```
/tocar [comando]           - Reproduz um áudio
/aprendido                 - Lista todos os áudios (com botões)
/aprender [cmd] [url]      - Adiciona novo áudio
/esquecer [comando]        - Remove um áudio
/sair                      - Desconecta do canal de voz
```

#### Playlists
```
/criar_playlist [nome]                          - Cria playlist
/adicionar_playlist [playlist] [audio]          - Adiciona áudio
/remover_playlist [playlist] [audio]            - Remove áudio
/ver_playlist [playlist]                        - Ver conteúdo
/listar_playlists                               - Listar todas
/tocar_playlist [playlist] [repetir] [aleatorio] - Tocar
/excluir_playlist [playlist]                    - Deletar
```

#### World of Warcraft
```
/wow [expansão]            - Navegar OST por expansão

Expansões suportadas:
- classic, tbc, wotlk, cataclysm, mop, wod, legion
- bfa, shadowlands, dragonflight, tww, undermine
```

#### Diversos
```
/piada                     - Conta uma piada
/status                    - Status do bot
/ajuda                     - Ajuda
```

---

## 🌐 API REST

A API completa está documentada em: **http://localhost:8080/docs**

### Exemplos

```bash
# Listar todos os áudios
GET /api/audios?guild_id=0

# Buscar áudio
GET /api/audios/search?q=ola

# Criar áudio
POST /api/audios
{
  "command": "teste",
  "file_path": "audio_clips/teste.mp3",
  "guild_id": 0
}

# Upload de arquivo
POST /api/audios/upload
Content-Type: multipart/form-data
- file: audio.mp3
- command: novo_audio
- guild_id: 0

# Estatísticas
GET /api/stats

# Playlists
GET /api/playlists?guild_id=0
POST /api/playlists
GET /api/playlists/{id}
DELETE /api/playlists/{id}
POST /api/playlists/{playlist_id}/audios/{audio_id}
```

---

## 🐳 Docker

### Arquitetura

```
cazalberto-bot    (Discord Bot)
   └── SQLite Database (volume compartilhado)
   └── Audio files (volume)

cazalberto-web    (Web Panel - porta 8080)
   └── SQLite Database (volume compartilhado)
   └── Audio files (volume)
```

### Comandos Úteis

```bash
# Ver logs
docker-compose -f docker-compose.new.yml logs -f bot
docker-compose -f docker-compose.new.yml logs -f web

# Restart services
docker-compose -f docker-compose.new.yml restart bot
docker-compose -f docker-compose.new.yml restart web

# Entrar no container
docker exec -it cazalberto-bot bash
docker exec -it cazalberto-web bash

# Rebuild
docker-compose -f docker-compose.new.yml build --no-cache
docker-compose -f docker-compose.new.yml up -d
```

---

## 💻 Desenvolvimento

### Estrutura do Projeto

```
cazalberto/
├── src/cazalberto/          # Código fonte
│   ├── core/                # Configuração, database, logging
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic (futuro)
│   ├── cogs/                # Discord cogs
│   ├── web/                 # FastAPI app
│   │   ├── templates/       # HTML templates
│   │   ├── app.py           # FastAPI app
│   │   └── api.py           # API endpoints
│   └── scripts/             # Utility scripts
├── tests/                   # Testes
│   ├── unit/                # Testes unitários
│   └── integration/         # Testes de integração
├── docker/                  # Dockerfiles
├── migrations/              # Alembic migrations (futuro)
└── pyproject.toml           # Poetry config
```

### Workflow de Desenvolvimento

```bash
# 1. Instalar pre-commit hooks
poetry run pre-commit install

# 2. Criar branch
git checkout -b feature/nova-funcionalidade

# 3. Desenvolver e testar
poetry run pytest -v
poetry run mypy src/

# 4. Formatar código
poetry run black src/ tests/
poetry run isort src/ tests/

# 5. Commit (hooks executarão automaticamente)
git add .
git commit -m "feat: adicionar nova funcionalidade"

# 6. Push
git push origin feature/nova-funcionalidade
```

### Executar Testes

```bash
# Todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=src/cazalberto --cov-report=html
open htmlcov/index.html

# Testes específicos
poetry run pytest tests/unit/test_audio_repository.py -v

# Com logs
poetry run pytest -v -s
```

### Adicionar Nova Funcionalidade

1. **Criar model** (se necessário) em `src/cazalberto/models/`
2. **Criar repository** em `src/cazalberto/repositories/`
3. **Adicionar endpoint** na API em `src/cazalberto/web/api.py`
4. **Criar comando** no cog apropriado em `src/cazalberto/cogs/`
5. **Escrever testes** em `tests/unit/`
6. **Atualizar documentação**

---

## 🔧 Configuração

### Variáveis de Ambiente (`.env`)

```env
# Discord
DISCORD_TOKEN=seu_token_aqui
DISCORD_PREFIX=!

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cazalberto.db

# Paths
AUDIO_CLIPS_PATH=./audio_clips
WOW_OST_PATH=./wow-ost
MAX_AUDIO_SIZE_MB=10

# Web
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_RELOAD=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/cazalberto.log

# Bot
BOT_VERSION=2.0.0
COMMAND_PREFIX=/
```

---

## 📊 CI/CD

### GitHub Actions Workflows

- **Lint & Type Check**: Black, isort, Ruff, mypy
- **Tests**: pytest com coverage
- **Docker Build**: Build de imagens
- **Security Scan**: Trivy vulnerability scanner

### Badges

```markdown
![Tests](https://github.com/danielgregorio/cazalberto/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/danielgregorio/cazalberto/branch/main/graph/badge.svg)
```

---

## 📈 Roadmap

### v2.1 (Próximo)
- [ ] Alembic migrations
- [ ] PostgreSQL support opcional
- [ ] Redis cache
- [ ] Autenticação no painel web
- [ ] Sistema de permissões por servidor
- [ ] Upload direto pelo painel web
- [ ] Player de áudio no painel
- [ ] Histórico de reprodução

### v2.2 (Futuro)
- [ ] Integração com Spotify
- [ ] Text-to-Speech
- [ ] Sistema de favoritos por usuário
- [ ] Playlist colaborativa
- [ ] API pública com rate limiting
- [ ] Mobile app (React Native)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: adicionar feature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais informações.

---

## 👤 Autor

**Daniel Gregorio**

- GitHub: [@danielgregorio](https://github.com/danielgregorio)
- Patreon: [Cazalberto](https://patreon.com/cazalberto)

---

## 🙏 Agradecimentos

- [discord.py](https://github.com/Rapptz/discord.py) - Framework Discord
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Alpine.js](https://alpinejs.dev/) - Frontend framework
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework

---

<div align="center">

**⭐ Se gostou do projeto, dê uma estrela no GitHub! ⭐**

[🐛 Reportar Bug](https://github.com/danielgregorio/cazalberto/issues) •
[💡 Sugerir Feature](https://github.com/danielgregorio/cazalberto/issues) •
[❓ FAQ](https://github.com/danielgregorio/cazalberto/wiki)

</div>
