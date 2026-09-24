import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from cazalberto.audio.download import download_audio
from cazalberto.errors import UserError


@pytest.fixture
async def server():
    async def audio(_):
        return web.Response(body=b"a" * 1000, content_type="audio/mpeg")

    async def html(_):
        return web.Response(text="<html></html>", content_type="text/html")

    async def missing(_):
        return web.Response(status=404)

    app = web.Application()
    app.router.add_get("/audio.mp3", audio)
    app.router.add_get("/page", html)
    app.router.add_get("/missing", missing)
    async with TestServer(app) as srv:
        yield srv


async def test_downloads_file(server, tmp_path):
    dest = tmp_path / "clips" / "x.mp3"
    async with aiohttp.ClientSession() as session:
        await download_audio(session, str(server.make_url("/audio.mp3")), dest, max_bytes=10_000)
    assert dest.read_bytes() == b"a" * 1000


@pytest.mark.parametrize(
    ("path", "max_bytes"),
    [("/audio.mp3", 500), ("/page", 10_000), ("/missing", 10_000)],
)
async def test_rejects_bad_downloads(server, tmp_path, path, max_bytes):
    dest = tmp_path / "x.mp3"
    async with aiohttp.ClientSession() as session:
        with pytest.raises(UserError):
            await download_audio(session, str(server.make_url(path)), dest, max_bytes=max_bytes)
    assert list(tmp_path.iterdir()) == []  # nada de arquivo pela metade


async def test_rejects_non_http_url(tmp_path):
    async with aiohttp.ClientSession() as session:
        with pytest.raises(UserError):
            await download_audio(session, "file:///etc/passwd", tmp_path / "x.mp3", max_bytes=10)
