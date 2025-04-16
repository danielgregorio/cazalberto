import discord
import os
import asyncio
import logging
import inspect
from discord.ext import commands
from config import TOKEN

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Configuração de Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Criar instância do bot
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_extensions():
    """Carrega todas as extensões (Cogs) da pasta cogs"""
    discovered_commands = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                module = f'cogs.{filename[:-3]}'
                await bot.load_extension(module)
                logging.info(f"✅ Carregado cog: {filename}")
                
                # Inspeciona os comandos do módulo
                cog = bot.get_cog(module.split('.')[-1].capitalize() + 'Commands')
                if cog:
                    for name, method in inspect.getmembers(cog):
                        if hasattr(method, '_discord_app_commands_param'):
                            discovered_commands.append(name)
            except Exception as e:
                logging.error(f"❌ Erro ao carregar {filename}: {e}")
    
    return discovered_commands

@bot.event
async def on_ready():
    logging.info(f"Bot conectado como {bot.user}")
    
    try:
        logging.info("Carregando extensões...")
        discovered_commands = await load_extensions()
        
        logging.info("Comandos descobertos:")
        for cmd in discovered_commands:
            logging.info(f"• {cmd}")
        
        logging.info("Sincronizando comandos globalmente...")
        synced = await bot.tree.sync()
        logging.info(f"✅ Sincronizados {len(synced)} comandos globalmente!")
        
        if len(synced) > 0:
            logging.info("Comandos sincronizados:")
            for command in synced:
                logging.info(f"• /{command.name}")
        else:
            logging.warning("⚠️ Nenhum comando foi sincronizado!")
    
    except Exception as e:
        logging.error(f"❌ Erro durante a sincronização: {e}")
    
    # Encerra o bot após a sincronização
    await bot.close()

async def main():
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        logging.info("Sincronização interrompida pelo usuário.")
    except Exception as e:
        logging.error(f"Erro: {e}")

if __name__ == "__main__":
    logging.info("Iniciando sincronização de comandos...")
    asyncio.run(main())
    logging.info("Sincronização concluída.")
    input("Pressione Enter para sair...")
