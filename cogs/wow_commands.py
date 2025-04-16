import discord
from discord.ext import commands
import logging

from config import COMMANDS_FILE
from utils import load_json

class WowCommands(commands.Cog):
    """Comandos relacionados aos áudios de World of Warcraft."""
    
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = load_json(COMMANDS_FILE)
        
        # Mapeamento de nomes de expansão e abreviações para prefixos
        self.expansion_prefixes = {
            # Números
            "0": "classic", "1": "tbc", "2": "wotlk", "3": "cata", 
            "4": "mop", "5": "wod", "6": "legion", "7": "bfa",
            "8": "sl", "9": "df", "10": "tww", "11": "undermine",
            
            # Nomes completos (em minúsculas)
            "classic": "classic",
            "vanilla": "classic",
            "tbc": "tbc", 
            "burning": "tbc",
            "crusade": "tbc",
            "wotlk": "wotlk",
            "lich": "wotlk",
            "wrath": "wotlk",
            "cata": "cata",
            "cataclysm": "cata",
            "mop": "mop",
            "mists": "mop",
            "pandaria": "mop",
            "wod": "wod",
            "draenor": "wod",
            "warlords": "wod",
            "legion": "legion",
            "bfa": "bfa",
            "battle": "bfa",
            "azeroth": "bfa",
            "sl": "sl",
            "shadowlands": "sl",
            "df": "df",
            "dragonflight": "df",
            "tww": "tww",
            "war": "tww",
            "within": "tww",
            "undermine": "undermine"
        }
        
        # Nomes amigáveis para exibição
        self.expansion_names = {
            "classic": "World of Warcraft: Classic",
            "tbc": "The Burning Crusade",
            "wotlk": "Wrath of the Lich King",
            "cata": "Cataclysm",
            "mop": "Mists of Pandaria",
            "wod": "Warlords of Draenor",
            "legion": "Legion",
            "bfa": "Battle for Azeroth",
            "sl": "Shadowlands",
            "df": "Dragonflight",
            "tww": "The War Within",
            "undermine": "Undermine"
        }

async def setup(bot):
    """Adiciona o cog ao bot."""
    await bot.add_cog(WowCommands(bot))
