"""
Testes de integração para API de áudios
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_audios_empty(test_app: AsyncClient) -> None:
    """Testa listagem de áudios quando vazio"""
    response = await test_app.get("/api/audios")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_audios(test_app_with_data: AsyncClient) -> None:
    """Testa listagem de áudios"""
    response = await test_app_with_data.get("/api/audios?guild_id=0")

    assert response.status_code == 200
    data = response.json()

    # Deve retornar os 3 áudios globais (guild_id=0)
    assert len(data) >= 3

    # Verificar estrutura
    assert "id" in data[0]
    assert "command" in data[0]
    assert "file_path" in data[0]
    assert "play_count" in data[0]


@pytest.mark.asyncio
async def test_search_audios(test_app_with_data: AsyncClient) -> None:
    """Testa busca de áudios"""
    response = await test_app_with_data.get("/api/audios/search?q=audio&guild_id=0")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    # Todos os resultados devem conter "audio" no comando
    assert all("audio" in item["command"] for item in data)


@pytest.mark.asyncio
async def test_search_audios_no_results(test_app_with_data: AsyncClient) -> None:
    """Testa busca sem resultados"""
    response = await test_app_with_data.get(
        "/api/audios/search?q=inexistente&guild_id=0"
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_audio_by_id(test_app_with_data: AsyncClient) -> None:
    """Testa busca de áudio por ID"""
    # Primeiro, listar para pegar um ID
    list_response = await test_app_with_data.get("/api/audios")
    audios = list_response.json()
    audio_id = audios[0]["id"]

    # Buscar por ID
    response = await test_app_with_data.get(f"/api/audios/{audio_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == audio_id
    assert "command" in data
    assert "file_path" in data


@pytest.mark.asyncio
async def test_get_audio_not_found(test_app: AsyncClient) -> None:
    """Testa busca de áudio inexistente"""
    response = await test_app.get("/api/audios/9999")

    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_audio(test_app: AsyncClient) -> None:
    """Testa criação de áudio"""
    payload = {
        "command": "novo_audio",
        "file_path": "audio_clips/novo.mp3",
        "guild_id": 0,
    }

    response = await test_app.post("/api/audios", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["command"] == "novo_audio"
    assert data["file_path"] == "audio_clips/novo.mp3"
    assert data["guild_id"] == 0
    assert data["play_count"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_create_audio_duplicate_command(test_app_with_data: AsyncClient) -> None:
    """Testa criação de áudio com comando duplicado"""
    payload = {
        "command": "audio0",  # Já existe
        "file_path": "audio_clips/teste.mp3",
        "guild_id": 0,
    }

    response = await test_app_with_data.post("/api/audios", json=payload)

    assert response.status_code == 400
    assert "já existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_audio(test_app_with_data: AsyncClient) -> None:
    """Testa atualização de áudio"""
    # Criar áudio primeiro
    create_response = await test_app_with_data.post(
        "/api/audios",
        json={
            "command": "update_test",
            "file_path": "audio_clips/original.mp3",
            "guild_id": 0,
        },
    )
    audio_id = create_response.json()["id"]

    # Atualizar
    update_payload = {
        "command": "updated_command",
        "file_path": "audio_clips/updated.mp3",
        "guild_id": 0,
    }

    response = await test_app_with_data.put(f"/api/audios/{audio_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["command"] == "updated_command"
    assert data["file_path"] == "audio_clips/updated.mp3"


@pytest.mark.asyncio
async def test_update_audio_not_found(test_app: AsyncClient) -> None:
    """Testa atualização de áudio inexistente"""
    payload = {
        "command": "test",
        "file_path": "test.mp3",
        "guild_id": 0,
    }

    response = await test_app.put("/api/audios/9999", json=payload)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_audio(test_app_with_data: AsyncClient) -> None:
    """Testa remoção de áudio"""
    # Criar áudio
    create_response = await test_app_with_data.post(
        "/api/audios",
        json={
            "command": "delete_test",
            "file_path": "audio_clips/delete.mp3",
            "guild_id": 0,
        },
    )
    audio_id = create_response.json()["id"]

    # Deletar
    response = await test_app_with_data.delete(f"/api/audios/{audio_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # Verificar que foi deletado
    get_response = await test_app_with_data.get(f"/api/audios/{audio_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_audio_not_found(test_app: AsyncClient) -> None:
    """Testa remoção de áudio inexistente"""
    response = await test_app.delete("/api/audios/9999")

    assert response.status_code == 404
