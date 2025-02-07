import discord
import aiohttp
import threading
import asyncio
from discord.ext import commands
from config import COMMANDS_FILE, AUDIO_FOLDER
from utils import load_json, save_json, logging
from voice import join_voice_channel, play_audio

custom_commands = load_json(COMMANDS_FILE)

bot = commands.Bot(intents=discord.Intents.default())

async def learn_sound(ctx, name, url):
    """Download and save a new sound, sending DM on success."""
    filename = f"{name}.mp3"
    filepath = os.path.join(AUDIO_FOLDER, filename)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(filepath, "wb") as f:
                        f.write(await resp.read())

                    custom_commands[name] = filename
                    save_json(COMMANDS_FILE, custom_commands)

                    try:
                        await ctx.author.send(f"✅ **Success!** `{name}` is ready!\nUse: `/tocar {name}`")
                    except discord.Forbidden:
                        logging.warning(f"⚠️ Could not send DM to {ctx.author}")

                    await ctx.respond(f"✅ `{name}` learned successfully!", ephemeral=True)

                else:
                    await ctx.respond(f"❌ Failed to download the file. HTTP Error {resp.status}.", ephemeral=True)

        except aiohttp.ClientError:
            await ctx.respond("❌ Error: Unable to reach the server. Please check the URL.", ephemeral=True)

@bot.slash_command(name="aprender", description="Teach the bot a new sound command")
async def aprender(ctx, name: str, url: str):
    if name in custom_commands:
        await ctx.respond(f"⚠️ Command `{name}` already exists.", ephemeral=True)
        return

    threading.Thread(target=lambda: asyncio.run_coroutine_threadsafe(learn_sound(ctx, name, url), bot.loop)).start()
    await ctx.respond(f"⏳ Learning `{name}`... Please wait!", ephemeral=True)

@bot.slash_command(name="tocar", description="Plays a saved sound")
async def tocar(ctx, name: str):
    if name in custom_commands:
        vc = ctx.voice_client or await join_voice_channel(ctx)
        if vc:
            await play_audio(vc, custom_commands[name])
            await ctx.respond(f"🔊 Now playing: `{name}`", ephemeral=True)
    else:
        await ctx.respond("❌ This sound does not exist!", ephemeral=True)

@bot.slash_command(name="sair", description="Makes the bot leave the voice channel")
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.respond("👋 Left the voice channel.", ephemeral=True)
    else:
        await ctx.respond("❌ I'm not in a voice channel!", ephemeral=True)
