"""
Testes de integração para API de playlists
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_playlists_empty(test_app: AsyncClient) -> None:
    """Testa listagem de playlists quando vazio"""
    response = await test_app.get("/api/playlists")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_playlists(test_app_with_data: AsyncClient) -> None:
    """Testa listagem de playlists"""
    response = await test_app_with_data.get("/api/playlists?guild_id=0")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0

    # Verificar estrutura
    assert "id" in data[0]
    assert "name" in data[0]
    assert "guild_id" in data[0]


@pytest.mark.asyncio
async def test_create_playlist(test_app: AsyncClient) -> None:
    """Testa criação de playlist"""
    payload = {
        "name": "Nova Playlist",
        "description": "Descrição da playlist",
        "guild_id": 0,
    }

    response = await test_app.post("/api/playlists", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Nova Playlist"
    assert data["description"] == "Descrição da playlist"
    assert data["guild_id"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_create_playlist_without_description(test_app: AsyncClient) -> None:
    """Testa criação de playlist sem descrição"""
    payload = {
        "name": "Sem Descrição",
        "guild_id": 0,
    }

    response = await test_app.post("/api/playlists", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Sem Descrição"
    assert data["description"] is None


@pytest.mark.asyncio
async def test_create_playlist_duplicate_name(test_app_with_data: AsyncClient) -> None:
    """Testa criação de playlist com nome duplicado"""
    payload = {
        "name": "Test Playlist",  # Já existe
        "guild_id": 0,
    }

    response = await test_app_with_data.post("/api/playlists", json=payload)

    assert response.status_code == 400
    assert "já existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_playlist(test_app_with_data: AsyncClient) -> None:
    """Testa busca de playlist por ID"""
    # Listar playlists
    list_response = await test_app_with_data.get("/api/playlists")
    playlists = list_response.json()
    playlist_id = playlists[0]["id"]

    # Buscar detalhes
    response = await test_app_with_data.get(f"/api/playlists/{playlist_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == playlist_id
    assert "name" in data
    assert "audios" in data
    assert isinstance(data["audios"], list)


@pytest.mark.asyncio
async def test_get_playlist_not_found(test_app: AsyncClient) -> None:
    """Testa busca de playlist inexistente"""
    response = await test_app.get("/api/playlists/9999")

    assert response.status_code == 404
    assert "não encontrada" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_playlist(test_app_with_data: AsyncClient) -> None:
    """Testa remoção de playlist"""
    # Criar playlist
    create_response = await test_app_with_data.post(
        "/api/playlists",
        json={"name": "Delete Test", "guild_id": 0},
    )
    playlist_id = create_response.json()["id"]

    # Deletar
    response = await test_app_with_data.delete(f"/api/playlists/{playlist_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verificar que foi deletada
    get_response = await test_app_with_data.get(f"/api/playlists/{playlist_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_playlist_not_found(test_app: AsyncClient) -> None:
    """Testa remoção de playlist inexistente"""
    response = await test_app.delete("/api/playlists/9999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_audio_to_playlist(test_app_with_data: AsyncClient) -> None:
    """Testa adição de áudio à playlist"""
    # Criar playlist e áudio
    playlist_response = await test_app_with_data.post(
        "/api/playlists",
        json={"name": "Add Audio Test", "guild_id": 0},
    )
    playlist_id = playlist_response.json()["id"]

    audio_response = await test_app_with_data.post(
        "/api/audios",
        json={
            "command": "test_audio",
            "file_path": "test.mp3",
            "guild_id": 0,
        },
    )
    audio_id = audio_response.json()["id"]

    # Adicionar áudio à playlist
    response = await test_app_with_data.post(
        f"/api/playlists/{playlist_id}/audios/{audio_id}"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "added"

    # Verificar que o áudio está na playlist
    playlist_detail = await test_app_with_data.get(f"/api/playlists/{playlist_id}")
    audios = playlist_detail.json()["audios"]

    assert len(audios) == 1
    assert audios[0]["id"] == audio_id


@pytest.mark.asyncio
async def test_remove_audio_from_playlist(test_app_with_data: AsyncClient) -> None:
    """Testa remoção de áudio da playlist"""
    # Criar playlist e áudio
    playlist_response = await test_app_with_data.post(
        "/api/playlists",
        json={"name": "Remove Audio Test", "guild_id": 0},
    )
    playlist_id = playlist_response.json()["id"]

    audio_response = await test_app_with_data.post(
        "/api/audios",
        json={
            "command": "remove_test",
            "file_path": "test.mp3",
            "guild_id": 0,
        },
    )
    audio_id = audio_response.json()["id"]

    # Adicionar áudio
    await test_app_with_data.post(f"/api/playlists/{playlist_id}/audios/{audio_id}")

    # Remover áudio
    response = await test_app_with_data.delete(
        f"/api/playlists/{playlist_id}/audios/{audio_id}"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "removed"

    # Verificar que foi removido
    playlist_detail = await test_app_with_data.get(f"/api/playlists/{playlist_id}")
    audios = playlist_detail.json()["audios"]

    assert len(audios) == 0


@pytest.mark.asyncio
async def test_remove_audio_from_playlist_not_found(
    test_app_with_data: AsyncClient,
) -> None:
    """Testa remoção de áudio que não está na playlist"""
    # Criar playlist
    playlist_response = await test_app_with_data.post(
        "/api/playlists",
        json={"name": "Not Found Test", "guild_id": 0},
    )
    playlist_id = playlist_response.json()["id"]

    # Tentar remover áudio inexistente
    response = await test_app_with_data.delete(
        f"/api/playlists/{playlist_id}/audios/9999"
    )

    assert response.status_code == 404
