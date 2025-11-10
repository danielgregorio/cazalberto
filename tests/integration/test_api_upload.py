"""
Testes de integração para upload de arquivos de áudio
"""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_audio_mp3(test_app: AsyncClient, tmp_path: Path) -> None:
    """Testa upload de arquivo MP3"""
    # Criar arquivo fake MP3
    file_content = b"fake mp3 content"
    files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
    data = {"command": "uploaded_audio", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 200
    result = response.json()

    assert result["status"] == "success"
    assert result["command"] == "uploaded_audio"
    assert "test.mp3" in result["file_path"]
    assert "id" in result


@pytest.mark.asyncio
async def test_upload_audio_wav(test_app: AsyncClient) -> None:
    """Testa upload de arquivo WAV"""
    file_content = b"fake wav content"
    files = {"file": ("test.wav", io.BytesIO(file_content), "audio/wav")}
    data = {"command": "wav_audio", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 200
    assert "test.wav" in response.json()["file_path"]


@pytest.mark.asyncio
async def test_upload_audio_ogg(test_app: AsyncClient) -> None:
    """Testa upload de arquivo OGG"""
    file_content = b"fake ogg content"
    files = {"file": ("test.ogg", io.BytesIO(file_content), "audio/ogg")}
    data = {"command": "ogg_audio", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_audio_m4a(test_app: AsyncClient) -> None:
    """Testa upload de arquivo M4A"""
    file_content = b"fake m4a content"
    files = {"file": ("test.m4a", io.BytesIO(file_content), "audio/mp4")}
    data = {"command": "m4a_audio", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_audio_invalid_extension(test_app: AsyncClient) -> None:
    """Testa upload de arquivo com extensão inválida"""
    file_content = b"fake content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    data = {"command": "invalid_audio", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 400
    assert "não suportado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_audio_duplicate_command(test_app: AsyncClient) -> None:
    """Testa upload com comando que já existe"""
    # Criar áudio primeiro
    await test_app.post(
        "/api/audios",
        json={
            "command": "duplicate_upload",
            "file_path": "existing.mp3",
            "guild_id": 0,
        },
    )

    # Tentar fazer upload com mesmo comando
    file_content = b"fake mp3 content"
    files = {"file": ("new.mp3", io.BytesIO(file_content), "audio/mpeg")}
    data = {"command": "duplicate_upload", "guild_id": "0"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 400
    assert "já existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_creates_database_entry(test_app: AsyncClient) -> None:
    """Testa que upload cria entrada no banco de dados"""
    file_content = b"fake mp3 content"
    files = {"file": ("database_test.mp3", io.BytesIO(file_content), "audio/mpeg")}
    data = {"command": "db_test", "guild_id": "0"}

    # Upload
    upload_response = await test_app.post("/api/audios/upload", files=files, data=data)
    assert upload_response.status_code == 200
    audio_id = upload_response.json()["id"]

    # Verificar que foi criado no banco
    get_response = await test_app.get(f"/api/audios/{audio_id}")
    assert get_response.status_code == 200

    audio_data = get_response.json()
    assert audio_data["command"] == "db_test"
    assert "database_test.mp3" in audio_data["file_path"]


@pytest.mark.asyncio
async def test_upload_with_custom_guild(test_app: AsyncClient) -> None:
    """Testa upload para servidor específico"""
    file_content = b"fake mp3 content"
    files = {"file": ("guild_test.mp3", io.BytesIO(file_content), "audio/mpeg")}
    data = {"command": "guild_audio", "guild_id": "123456"}

    response = await test_app.post("/api/audios/upload", files=files, data=data)

    assert response.status_code == 200

    # Verificar guild_id
    audio_id = response.json()["id"]
    get_response = await test_app.get(f"/api/audios/{audio_id}")

    assert get_response.json()["guild_id"] == 123456


@pytest.mark.asyncio
async def test_upload_multiple_files_different_commands(test_app: AsyncClient) -> None:
    """Testa upload de múltiplos arquivos"""
    uploads = [
        ("multi1.mp3", "multi_cmd1"),
        ("multi2.mp3", "multi_cmd2"),
        ("multi3.wav", "multi_cmd3"),
    ]

    for filename, command in uploads:
        file_content = b"fake audio content"
        files = {"file": (filename, io.BytesIO(file_content), "audio/mpeg")}
        data = {"command": command, "guild_id": "0"}

        response = await test_app.post("/api/audios/upload", files=files, data=data)
        assert response.status_code == 200

    # Verificar que todos foram criados
    list_response = await test_app.get("/api/audios")
    audios = list_response.json()

    assert len(audios) >= 3
    commands = [a["command"] for a in audios]
    assert "multi_cmd1" in commands
    assert "multi_cmd2" in commands
    assert "multi_cmd3" in commands
