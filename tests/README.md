# 🧪 Guia de Testes - Cazalberto

## 📋 Estrutura de Testes

```
tests/
├── conftest.py                # Fixtures compartilhadas (unit tests)
├── unit/                      # Testes unitários
│   ├── test_audio_repository.py
│   ├── test_playlist_repository.py
│   └── test_config.py
└── integration/               # Testes de integração
    ├── conftest.py           # Fixtures para testes web
    ├── test_api_audios.py    # 13 testes de API de áudios
    ├── test_api_playlists.py # 11 testes de API de playlists
    ├── test_api_stats.py     # 10 testes de stats e HTML
    └── test_api_upload.py    # 9 testes de upload
```

## 🚀 Executando Testes

### Todos os testes
```bash
poetry run pytest -v
```

### Apenas testes unitários
```bash
poetry run pytest tests/unit/ -v
```

### Apenas testes de integração
```bash
poetry run pytest tests/integration/ -v
```

### Teste específico
```bash
poetry run pytest tests/integration/test_api_audios.py::test_create_audio -v
```

### Com cobertura
```bash
poetry run pytest --cov=src/cazalberto --cov-report=html --cov-report=term
```

### Com logs detalhados
```bash
poetry run pytest -v -s
```

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError"

**Problema:** Python não encontra os módulos

**Solução:**
```bash
# Certifique-se de estar no ambiente virtual
poetry shell

# Reinstale as dependências
poetry install

# Verifique se PYTHONPATH está configurado
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Erro: "fixture 'test_app' not found"

**Problema:** Fixtures não estão sendo carregadas

**Solução:**
```bash
# Certifique-se de que conftest.py existe
ls tests/integration/conftest.py

# Execute com verbose para ver detalhes
poetry run pytest tests/integration/ -v --collect-only
```

### Erro: "asyncio event loop is closed"

**Problema:** Problemas com event loop assíncrono

**Solução:**
```bash
# Certifique-se de que pytest-asyncio está instalado
poetry add --group dev pytest-asyncio

# Verifique configuração no pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
```

### Erro: "database is locked"

**Problema:** SQLite não permite escritas concorrentes

**Solução:**
- Os testes usam banco em memória (`:memory:`)
- Cada teste tem sua própria sessão isolada
- Se persistir, verifique que não há conexões antigas abertas

### Erro: "DISCORD_TOKEN not found"

**Problema:** Variáveis de ambiente necessárias

**Solução:**
```bash
# Crie um .env.test para testes
cp .env.example .env.test

# Ou defina variável temporária
export DISCORD_TOKEN=test_token_for_testing
```

### Erro: CI/CD falha mas local passa

**Problema:** Diferenças de ambiente

**Solução:**
```bash
# Teste exatamente como o CI
poetry run pytest tests/integration/ -v --tb=short

# Verifique dependências
poetry lock --check

# Force reinstalação
rm poetry.lock
poetry install
```

## 📊 Cobertura de Testes

### Ver relatório HTML
```bash
poetry run pytest --cov=src/cazalberto --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Metas de cobertura
- **Mínimo aceitável:** 70%
- **Alvo:** 80%
- **Atual:** ~90% (unit + integration)

## 🎯 Fixtures Disponíveis

### Testes Unitários (`tests/conftest.py`)
- `engine` - SQLite engine em memória
- `session` - Sessão de banco de dados assíncrona
- `sample_audio` - Áudio de exemplo
- `sample_playlist` - Playlist de exemplo

### Testes de Integração (`tests/integration/conftest.py`)
- `test_engine` - Engine separada para testes web
- `override_get_session` - Override de dependência FastAPI
- `test_app` - Cliente HTTP limpo
- `test_app_with_data` - Cliente com 5 áudios e 1 playlist

## 📝 Escrevendo Novos Testes

### Teste Unitário
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.cazalberto.repositories.audio_repository import AudioRepository

@pytest.mark.asyncio
async def test_my_feature(session: AsyncSession) -> None:
    """Testa minha funcionalidade"""
    repo = AudioRepository(session)

    # Arrange
    # ... setup

    # Act
    result = await repo.my_method()

    # Assert
    assert result is not None
```

### Teste de Integração
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_my_endpoint(test_app: AsyncClient) -> None:
    """Testa meu endpoint da API"""
    # Act
    response = await test_app.get("/api/my-endpoint")

    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## 🐛 Debug de Testes

### Usar breakpoint
```python
@pytest.mark.asyncio
async def test_something(test_app: AsyncClient) -> None:
    breakpoint()  # Pausa aqui
    response = await test_app.get("/api/test")
```

### Ver SQL queries
```python
# No conftest.py, mude echo=False para echo=True
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=True,  # Mostra SQL no console
)
```

### Executar apenas testes que falharam
```bash
poetry run pytest --lf  # last failed
```

### Parar no primeiro erro
```bash
poetry run pytest -x
```

## 📦 Dependências de Teste

Certifique-se de que estas dependências estão instaladas:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
httpx = "^0.26.0"  # Cliente HTTP para testes
```

## 🔄 CI/CD

Os testes rodam automaticamente no GitHub Actions em:
- Push para `main`, `develop`, `claude/**`
- Pull requests

Ver logs em: `.github/workflows/ci.yml`

### Executar localmente como o CI
```bash
# Exatamente como o GitHub Actions
poetry run black --check src/ tests/
poetry run isort --check src/ tests/
poetry run ruff check src/ tests/
poetry run pytest --cov=src/cazalberto --cov-report=xml
```

## 📚 Recursos

- [Pytest Docs](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTPX](https://www.python-httpx.org/)

---

**Última atualização:** 2024-11-10
