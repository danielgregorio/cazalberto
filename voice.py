import discord
import os
from config import AUDIO_FOLDER
from utils import logging

async def join_voice_channel(ctx)
    Ensure the bot joins a voice channel.
    if ctx.author.voice
        return await ctx.author.voice.channel.connect()
    else
        await ctx.respond(❌ You must be in a voice channel!, ephemeral=True)
        return None

async def play_audio(vc, filename)
    Play an audio file in a voice channel.
    filepath = os.path.join(AUDIO_FOLDER, filename)
    if os.path.exists(filepath)
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(filepath))
    else
        logging.warning(f⚠️ File {filename} not found.)
