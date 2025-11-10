"""
API endpoints para o painel web
"""

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..models.audio import Audio, Playlist
from ..repositories.audio_repository import AudioRepository
from ..repositories.playlist_repository import PlaylistRepository

router = APIRouter()


# Schemas Pydantic
class AudioCreate(BaseModel):
    command: str
    file_path: str
    guild_id: int = 0


class AudioResponse(BaseModel):
    id: int
    command: str
    file_path: str
    guild_id: int
    play_count: int
    added_by: int

    class Config:
        from_attributes = True


class PlaylistCreate(BaseModel):
    name: str
    description: str | None = None
    guild_id: int = 0


class PlaylistResponse(BaseModel):
    id: int
    name: str
    description: str | None
    guild_id: int
    created_by: int

    class Config:
        from_attributes = True


# ========== ENDPOINTS DE ÁUDIOS ==========


@router.get("/audios", response_model=list[AudioResponse])
async def list_audios(
    guild_id: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[Audio]:
    """Lista todos os áudios"""
    repo = AudioRepository(session)
    audios = await repo.list_by_guild(guild_id, include_global=True)
    return audios


@router.get("/audios/search")
async def search_audios(
    q: str,
    guild_id: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Busca áudios por comando"""
    repo = AudioRepository(session)
    audios = await repo.search_by_command(q, guild_id)

    return [
        {
            "id": a.id,
            "command": a.command,
            "file_path": a.file_path,
            "play_count": a.play_count,
        }
        for a in audios
    ]


@router.get("/audios/{audio_id}", response_model=AudioResponse)
async def get_audio(
    audio_id: int,
    session: AsyncSession = Depends(get_session),
) -> Audio:
    """Busca um áudio por ID"""
    repo = AudioRepository(session)
    audio = await repo.get(audio_id)

    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado")

    return audio


@router.post("/audios", response_model=AudioResponse, status_code=201)
async def create_audio(
    data: AudioCreate,
    session: AsyncSession = Depends(get_session),
) -> Audio:
    """Cria um novo áudio"""
    repo = AudioRepository(session)

    # Verificar se comando já existe
    if await repo.command_exists(data.command, data.guild_id):
        raise HTTPException(status_code=400, detail="Comando já existe")

    # Criar áudio
    audio = Audio(
        command=data.command,
        file_path=data.file_path,
        guild_id=data.guild_id,
        added_by=0,  # System/Web
    )

    session.add(audio)
    await session.commit()
    await session.refresh(audio)

    return audio


@router.put("/audios/{audio_id}", response_model=AudioResponse)
async def update_audio(
    audio_id: int,
    data: AudioCreate,
    session: AsyncSession = Depends(get_session),
) -> Audio:
    """Atualiza um áudio"""
    repo = AudioRepository(session)
    audio = await repo.get(audio_id)

    if not audio:
        raise HTTPException(status_code=404, detail="Áudio não encontrado")

    # Atualizar campos
    audio.command = data.command
    audio.file_path = data.file_path
    audio.guild_id = data.guild_id

    await session.commit()
    await session.refresh(audio)

    return audio


@router.delete("/audios/{audio_id}")
async def delete_audio(
    audio_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Remove um áudio"""
    repo = AudioRepository(session)

    if await repo.delete(audio_id):
        return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="Áudio não encontrado")


@router.post("/audios/upload")
async def upload_audio(
    file: UploadFile = File(...),
    command: str = Form(...),
    guild_id: int = Form(0),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Upload de arquivo de áudio"""
    import aiofiles
    from pathlib import Path

    from ..core.config import settings

    # Validar extensão
    allowed_extensions = {".mp3", ".wav", ".ogg", ".m4a"}
    file_ext = Path(file.filename or "").suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}",
        )

    # Salvar arquivo
    settings.audio_clips_path.mkdir(parents=True, exist_ok=True)
    file_path = settings.audio_clips_path / (file.filename or "audio.mp3")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Criar registro no banco
    repo = AudioRepository(session)

    if await repo.command_exists(command, guild_id):
        raise HTTPException(status_code=400, detail="Comando já existe")

    audio = Audio(
        command=command,
        file_path=str(file_path),
        guild_id=guild_id,
        added_by=0,
    )

    session.add(audio)
    await session.commit()

    return {
        "status": "success",
        "id": audio.id,
        "command": command,
        "file_path": str(file_path),
    }


# ========== ENDPOINTS DE PLAYLISTS ==========


@router.get("/playlists", response_model=list[PlaylistResponse])
async def list_playlists(
    guild_id: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[Playlist]:
    """Lista todas as playlists"""
    repo = PlaylistRepository(session)
    playlists = await repo.list_by_guild(guild_id)
    return playlists


@router.get("/playlists/{playlist_id}")
async def get_playlist(
    playlist_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Busca uma playlist com seus áudios"""
    repo = PlaylistRepository(session)
    playlist = await repo.get_with_items(playlist_id)

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist não encontrada")

    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "guild_id": playlist.guild_id,
        "audios": [
            {
                "id": item.audio.id,
                "command": item.audio.command,
                "file_path": item.audio.file_path,
                "position": item.position,
            }
            for item in playlist.items
        ],
    }


@router.post("/playlists", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    data: PlaylistCreate,
    session: AsyncSession = Depends(get_session),
) -> Playlist:
    """Cria uma nova playlist"""
    repo = PlaylistRepository(session)

    # Verificar se já existe
    if await repo.playlist_exists(data.name, data.guild_id):
        raise HTTPException(status_code=400, detail="Playlist já existe")

    # Criar playlist
    playlist = Playlist(
        name=data.name,
        description=data.description,
        guild_id=data.guild_id,
        created_by=0,
    )

    session.add(playlist)
    await session.commit()
    await session.refresh(playlist)

    return playlist


@router.delete("/playlists/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Remove uma playlist"""
    repo = PlaylistRepository(session)

    if await repo.delete(playlist_id):
        return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="Playlist não encontrada")


@router.post("/playlists/{playlist_id}/audios/{audio_id}")
async def add_audio_to_playlist(
    playlist_id: int,
    audio_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Adiciona um áudio à playlist"""
    repo = PlaylistRepository(session)

    try:
        await repo.add_audio(playlist_id, audio_id)
        return {"status": "added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/playlists/{playlist_id}/audios/{audio_id}")
async def remove_audio_from_playlist(
    playlist_id: int,
    audio_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Remove um áudio da playlist"""
    repo = PlaylistRepository(session)

    if await repo.remove_audio(playlist_id, audio_id):
        return {"status": "removed"}

    raise HTTPException(status_code=404, detail="Áudio não encontrado na playlist")


# ========== ESTATÍSTICAS ==========


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Retorna estatísticas gerais"""
    audio_repo = AudioRepository(session)
    playlist_repo = PlaylistRepository(session)

    total_audios = await audio_repo.count()
    total_playlists = await playlist_repo.count()

    return {
        "total_audios": total_audios,
        "total_playlists": total_playlists,
    }
