# 🚀 Guia de Migração - Cazalberto v2.0

Este guia explica como migrar do Cazalberto v1.x para a versão 2.0 modernizada.

## 📋 Sumário

- [O que mudou](#o-que-mudou)
- [Pré-requisitos](#pré-requisitos)
- [Passo a Passo](#passo-a-passo)
- [Usando o Painel Web](#usando-o-painel-web)
- [Docker](#docker)
- [Desenvolvimento](#desenvolvimento)
- [Resolução de Problemas](#resolução-de-problemas)

---

## 🔄 O que mudou

### Versão 1.x → 2.0

| Recurso | v1.x | v2.0 |
|---------|------|------|
| **Gerenciamento de Deps** | requirements.txt | Poetry |
| **Banco de Dados** | JSON | SQLite (SQLAlchemy) |
| **Configuração** | Hardcoded | Pydantic Settings + .env |
| **Type Hints** | Parcial | Completo (mypy) |
| **Testes** | ❌ Nenhum | ✅ pytest + coverage |
| **CI/CD** | ❌ Nenhum | ✅ GitHub Actions |
| **Painel Web** | ❌ Nenhum | ✅ FastAPI + Alpine.js |
| **Code Quality** | ❌ Manual | ✅ Black + Ruff + pre-commit |
| **Paths** | ⚠️ Windows hardcoded | ✅ Multiplataforma |

---

## 📦 Pré-requisitos

- **Python 3.11+**
- **Poetry** (gerenciador de dependências)
- **FFmpeg** (para áudio)
- **Docker** (opcional, para containerização)

### Instalar Poetry

```bash
# Linux/macOS/WSL
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

Adicione o Poetry ao PATH:
```bash
# Linux/macOS
export PATH="$HOME/.local/bin:$PATH"

# Windows: Adicionar %APPDATA%\Python\Scripts ao PATH
```

---

## 🔧 Passo a Passo

### 1. Backup dos Dados Atuais

```bash
# Fazer backup dos arquivos JSON
cp commands.json commands_backup.json
cp playlists.json playlists_backup.json

# Backup dos áudios
cp -r audio_clips audio_clips_backup
```

### 2. Instalar Dependências

```bash
# Instalar dependências do projeto
poetry install

# Ativar ambiente virtual
poetry shell
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
nano .env  # ou vim, code, etc.
```

Configurações importantes no `.env`:
```env
DISCORD_TOKEN=seu_token_aqui
DATABASE_URL=sqlite+aiosqlite:///./data/cazalberto.db
AUDIO_CLIPS_PATH=./audio_clips
WOW_OST_PATH=./wow-ost  # Ajustar para seu caminho
WEB_PORT=8080
LOG_LEVEL=INFO
```

### 4. Inicializar Banco de Dados

```bash
# Criar tabelas do banco de dados
poetry run python -m src.cazalberto.scripts.init_db
```

### 5. Migrar Dados JSON → SQLite

```bash
# Migrar comandos e playlists
poetry run python -m src.cazalberto.scripts.migrate_json_to_db \
  --commands-json commands.json \
  --playlists-json playlists.json

# Saída esperada:
# ✓ 65 comandos migrados
# ✓ 3 playlists migradas
```

### 6. Instalar Pre-commit Hooks (Opcional, para desenvolvimento)

```bash
poetry run pre-commit install
```

### 7. Executar o Bot

```bash
# Apenas o bot Discord
poetry run python -m src.cazalberto.bot

# Ou usando o script do Poetry
poetry run cazalberto
```

### 8. Executar o Painel Web (em terminal separado)

```bash
# Painel web
poetry run python -m src.cazalberto.web.app

# Ou usando uvicorn diretamente
poetry run uvicorn src.cazalberto.web.app:app --host 0.0.0.0 --port 8080 --reload
```

Acesse: **http://localhost:8080**

---

## 🌐 Usando o Painel Web

### Dashboard
- Visualize estatísticas gerais (total de áudios, playlists)
- Acesse rapidamente as funcionalidades

### Gerenciar Áudios (`/audios`)
- ✅ Listar todos os áudios
- ✅ Buscar por comando
- ✅ Adicionar novos áudios
- ✅ Excluir áudios
- ✅ Upload de arquivos (em breve)

### Gerenciar Playlists (`/playlists`)
- ✅ Criar playlists
- ✅ Ver detalhes e áudios
- ✅ Excluir playlists
- ✅ Adicionar/remover áudios (em breve)

### API REST

A API está documentada em: **http://localhost:8080/docs**

Exemplos de endpoints:
```bash
# Listar áudios
curl http://localhost:8080/api/audios

# Buscar áudio
curl http://localhost:8080/api/audios/search?q=ola

# Criar áudio
curl -X POST http://localhost:8080/api/audios \
  -H "Content-Type: application/json" \
  -d '{"command":"teste","file_path":"audio_clips/teste.mp3","guild_id":0}'

# Estatísticas
curl http://localhost:8080/api/stats
```

---

## 🐳 Docker

### Usando Docker Compose (Recomendado)

```bash
# Build e start
docker-compose -f docker-compose.new.yml up -d

# Ver logs
docker-compose -f docker-compose.new.yml logs -f

# Parar
docker-compose -f docker-compose.new.yml down
```

Services disponíveis:
- **bot**: Bot Discord (`cazalberto-bot`)
- **web**: Painel Web (`cazalberto-web`) - porta 8080

### Build Manual

```bash
# Build bot
docker build -f docker/bot.Dockerfile -t cazalberto-bot:latest .

# Build web
docker build -f docker/web.Dockerfile -t cazalberto-web:latest .

# Run bot
docker run -d --name cazalberto-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/audio_clips:/app/audio_clips \
  -v $(pwd)/logs:/app/logs \
  cazalberto-bot:latest

# Run web
docker run -d --name cazalberto-web \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/audio_clips:/app/audio_clips \
  cazalberto-web:latest
```

---

## 💻 Desenvolvimento

### Executar Testes

```bash
# Todos os testes
poetry run pytest

# Com cobertura
poetry run pytest --cov=src/cazalberto --cov-report=html

# Apenas um arquivo
poetry run pytest tests/unit/test_audio_repository.py

# Modo verbose
poetry run pytest -v
```

### Linting e Formatação

```bash
# Formatar código
poetry run black src/ tests/
poetry run isort src/ tests/

# Verificar
poetry run black --check src/
poetry run ruff check src/

# Type checking
poetry run mypy src/
```

### Executar com Hot Reload

```bash
# Bot (com auto-restart)
poetry run watchmedo auto-restart --directory=src --pattern=*.py --recursive \
  -- python -m src.cazalberto.bot

# Web (reload automático)
poetry run uvicorn src.cazalberto.web.app:app --reload
```

---

## 🔧 Resolução de Problemas

### Erro: "Module not found"

```bash
# Reinstalar dependências
poetry install --no-root

# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Erro: "Database locked"

O SQLite permite apenas uma escrita por vez. Certifique-se de que:
- Apenas uma instância do bot está rodando
- O painel web e bot não competem pelo banco

### Erro: "FFmpeg not found"

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Baixar de: https://ffmpeg.org/download.html
```

### Erro: "Discord token invalid"

Verifique se o token no `.env` está correto:
```bash
cat .env | grep DISCORD_TOKEN
```

### Migração não encontra arquivos

Certifique-se de que os paths no JSON estão corretos:
```bash
# Ver conteúdo do JSON
cat commands.json | jq '.[0:3]'
```

### Painel web não abre

```bash
# Verificar se a porta está em uso
lsof -i :8080

# Mudar porta no .env
WEB_PORT=8081
```

---

## 📚 Recursos Adicionais

- **Documentação API**: http://localhost:8080/docs
- **GitHub**: https://github.com/danielgregorio/cazalberto
- **Issues**: https://github.com/danielgregorio/cazalberto/issues

---

## 🎉 Próximos Passos

Após a migração bem-sucedida:

1. **Testar funcionalidades básicas**
   - /tocar [comando]
   - /aprendido
   - /tocar_playlist

2. **Explorar o painel web**
   - Adicionar/remover áudios
   - Criar playlists
   - Visualizar estatísticas

3. **Configurar CI/CD**
   - Push para GitHub
   - Verificar workflows
   - Configurar Codecov (opcional)

4. **Deploy em produção**
   - Usar Docker Compose
   - Configurar volumes persistentes
   - Setup de backup automático

---

## 🤝 Contribuindo

Se encontrar bugs ou tiver sugestões:
1. Abra uma issue no GitHub
2. Envie um Pull Request
3. Siga o guia de contribuição em CONTRIBUTING.md

---

**Feito com ❤️ por Daniel Gregorio**
