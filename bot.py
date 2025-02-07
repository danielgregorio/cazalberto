from discord.ext import commands
from config import TOKEN
from commands import bot  # Import bot instance from commands.py
import logging

@bot.event
async def on_ready():
    logging.info(f"✅ Cazalberto is online as {bot.user}")

# Run the bot
bot.run(TOKEN)
