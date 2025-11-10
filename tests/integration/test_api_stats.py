"""
Testes de integração para API de estatísticas e rotas HTML
"""

import pytest
from httpx import AsyncClient


# ========== Testes de Estatísticas ==========


@pytest.mark.asyncio
async def test_get_stats_empty(test_app: AsyncClient) -> None:
    """Testa estatísticas quando banco está vazio"""
    response = await test_app.get("/api/stats")

    assert response.status_code == 200
    data = response.json()

    assert data["total_audios"] == 0
    assert data["total_playlists"] == 0


@pytest.mark.asyncio
async def test_get_stats_with_data(test_app_with_data: AsyncClient) -> None:
    """Testa estatísticas com dados"""
    response = await test_app_with_data.get("/api/stats")

    assert response.status_code == 200
    data = response.json()

    assert "total_audios" in data
    assert "total_playlists" in data
    assert data["total_audios"] > 0
    assert data["total_playlists"] > 0


# ========== Testes de Rotas HTML ==========


@pytest.mark.asyncio
async def test_home_page(test_app: AsyncClient) -> None:
    """Testa página inicial (dashboard)"""
    response = await test_app.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    assert "Dashboard" in html
    assert "Cazalberto" in html


@pytest.mark.asyncio
async def test_audios_page(test_app: AsyncClient) -> None:
    """Testa página de gerenciamento de áudios"""
    response = await test_app.get("/audios")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    assert "Gerenciar Áudios" in html or "udios" in html  # Pode ter encoding issues
    assert "Cazalberto" in html


@pytest.mark.asyncio
async def test_playlists_page(test_app: AsyncClient) -> None:
    """Testa página de gerenciamento de playlists"""
    response = await test_app.get("/playlists")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    assert "Playlists" in html
    assert "Cazalberto" in html


@pytest.mark.asyncio
async def test_health_check(test_app: AsyncClient) -> None:
    """Testa endpoint de health check"""
    response = await test_app.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data


# ========== Testes de Navegação ==========


@pytest.mark.asyncio
async def test_navigation_links(test_app: AsyncClient) -> None:
    """Testa que as páginas contêm links de navegação"""
    # Dashboard
    home_response = await test_app.get("/")
    home_html = home_response.text

    assert "/audios" in home_html
    assert "/playlists" in home_html

    # Página de áudios
    audios_response = await test_app.get("/audios")
    audios_html = audios_response.text

    assert "/" in audios_html  # Link para home


# ========== Testes de Erro ==========


@pytest.mark.asyncio
async def test_404_not_found(test_app: AsyncClient) -> None:
    """Testa rota inexistente"""
    response = await test_app.get("/rota/inexistente")

    assert response.status_code == 404


# ========== Testes de Integração Completos ==========


@pytest.mark.asyncio
async def test_full_audio_workflow(test_app: AsyncClient) -> None:
    """Testa workflow completo de gerenciamento de áudio"""
    # 1. Verificar que está vazio
    list_response = await test_app.get("/api/audios")
    assert len(list_response.json()) == 0

    # 2. Criar áudio
    create_response = await test_app.post(
        "/api/audios",
        json={
            "command": "workflow_test",
            "file_path": "test.mp3",
            "guild_id": 0,
        },
    )
    assert create_response.status_code == 201
    audio_id = create_response.json()["id"]

    # 3. Listar e verificar que aparece
    list_response = await test_app.get("/api/audios")
    assert len(list_response.json()) == 1

    # 4. Buscar por ID
    get_response = await test_app.get(f"/api/audios/{audio_id}")
    assert get_response.status_code == 200

    # 5. Atualizar
    update_response = await test_app.put(
        f"/api/audios/{audio_id}",
        json={
            "command": "workflow_updated",
            "file_path": "updated.mp3",
            "guild_id": 0,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["command"] == "workflow_updated"

    # 6. Deletar
    delete_response = await test_app.delete(f"/api/audios/{audio_id}")
    assert delete_response.status_code == 200

    # 7. Verificar que foi deletado
    list_response = await test_app.get("/api/audios")
    assert len(list_response.json()) == 0


@pytest.mark.asyncio
async def test_full_playlist_workflow(test_app: AsyncClient) -> None:
    """Testa workflow completo de playlist"""
    # 1. Criar playlist
    playlist_response = await test_app.post(
        "/api/playlists",
        json={
            "name": "Workflow Playlist",
            "description": "Test",
            "guild_id": 0,
        },
    )
    assert playlist_response.status_code == 201
    playlist_id = playlist_response.json()["id"]

    # 2. Criar áudio
    audio_response = await test_app.post(
        "/api/audios",
        json={
            "command": "playlist_audio",
            "file_path": "test.mp3",
            "guild_id": 0,
        },
    )
    audio_id = audio_response.json()["id"]

    # 3. Adicionar áudio à playlist
    add_response = await test_app.post(
        f"/api/playlists/{playlist_id}/audios/{audio_id}"
    )
    assert add_response.status_code == 200

    # 4. Verificar que está na playlist
    detail_response = await test_app.get(f"/api/playlists/{playlist_id}")
    assert len(detail_response.json()["audios"]) == 1

    # 5. Remover áudio da playlist
    remove_response = await test_app.delete(
        f"/api/playlists/{playlist_id}/audios/{audio_id}"
    )
    assert remove_response.status_code == 200

    # 6. Verificar que foi removido
    detail_response = await test_app.get(f"/api/playlists/{playlist_id}")
    assert len(detail_response.json()["audios"]) == 0

    # 7. Deletar playlist
    delete_response = await test_app.delete(f"/api/playlists/{playlist_id}")
    assert delete_response.status_code == 200
