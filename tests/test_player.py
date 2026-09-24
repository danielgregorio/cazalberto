import asyncio

import pytest

from cazalberto.audio import player as player_module
from cazalberto.audio.player import VoicePlayer


class FakeGuild:
    id = 1
    name = "servidor"


class FakeVoiceClient:
    """Simula o VoiceClient: 'toca' cada áudio por um instante e chama o `after`."""

    def __init__(self):
        self.guild = FakeGuild()
        self.played = []
        self._playing = False

    def is_connected(self):
        return True

    def is_playing(self):
        return self._playing

    def is_paused(self):
        return False

    def stop(self):
        self._playing = False

    def play(self, source, after):
        self.played.append(source)
        self._playing = True
        loop = asyncio.get_running_loop()

        def finish():
            self._playing = False
            after(None)

        loop.call_later(0.01, finish)


@pytest.fixture(autouse=True)
def fake_ffmpeg(monkeypatch):
    monkeypatch.setattr(player_module.discord, "FFmpegPCMAudio", lambda path: path)


def _files(tmp_path, *names):
    items = []
    for name in names:
        path = tmp_path / f"{name}.mp3"
        path.write_bytes(b"")
        items.append((name, path))
    return items


async def test_queue_plays_in_order_and_repeats(tmp_path):
    vc = FakeVoiceClient()
    player = VoicePlayer(bot=None)
    items = _files(tmp_path, "a", "b")
    announced, done = [], asyncio.Event()

    async def on_track(name):
        announced.append(name)

    async def on_finish():
        done.set()

    player.start_queue(vc, items, repeat=2, on_track=on_track, on_finish=on_finish)
    await asyncio.wait_for(done.wait(), 2)
    assert announced == ["a", "b", "a", "b"]
    assert vc.played == [str(p) for _, p in items] * 2


async def test_missing_files_are_skipped(tmp_path):
    vc = FakeVoiceClient()
    player = VoicePlayer(bot=None)
    items = [("sumiu", tmp_path / "sumiu.mp3"), *_files(tmp_path, "ok")]
    done = asyncio.Event()

    async def on_finish():
        done.set()

    player.start_queue(vc, items, on_finish=on_finish)
    await asyncio.wait_for(done.wait(), 2)
    assert vc.played == [str(tmp_path / "ok.mp3")]


async def test_new_queue_cancels_previous(tmp_path):
    vc = FakeVoiceClient()
    player = VoicePlayer(bot=None)
    player.start_queue(vc, _files(tmp_path, "a", "b", "c"), repeat=5)
    await asyncio.sleep(0)
    assert player.cancel_queue(vc.guild.id)
    assert not player.cancel_queue(vc.guild.id)
