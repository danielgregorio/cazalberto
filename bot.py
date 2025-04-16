import os
import logging
import asyncio
import discord
from discord.ext import commands
from config import TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configuração de Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Criar instância do bot
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_extensions():
    """Carrega todas as extensões (Cogs) da pasta cogs de forma assíncrona"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f"✅ Carregado cog: {filename}")
            except commands.ExtensionAlreadyLoaded:
                logging.warning(f"⚠️ Cog {filename} já carregado.")
            except commands.errors.CommandRegistrationError as e:
                logging.warning(f"⚠️ Erro ao registrar comandos em {filename}: {e}")
            except Exception as e:
                logging.error(f"❌ Erro ao carregar {filename}: {e}")

@bot.event
async def on_ready():
    """Evento chamado quando o bot está pronto"""
    logging.info(f"✅ Conectado como {bot.user}")
    logging.info(f"✅ ID: {bot.user.id}")
    
    # Sincroniza comandos após estar pronto
    try:
        await bot.tree.sync()
        logging.info("✅ Comandos slash sincronizados!")
    except Exception as e:
        logging.error(f"❌ Erro ao sincronizar comandos: {e}")

async def main():
    """Função principal para iniciar o bot"""
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
