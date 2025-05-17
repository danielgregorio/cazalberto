import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Token
TOKEN = os.getenv("DISCORD_TOKEN")

# File Paths
AUDIO_FOLDER = "audio_clips"
COMMANDS_FILE = "commands.json"
GREETINGS_FILE = "greetings.json"
PLAYLISTS_FILE = "playlists.json"

# Joke System
JOKES_FILE = "jokes.json"
ICEBREAKER_FILE = "icebreaker.json"
DEFAULT_JOKE_INTERVAL = 15  # Default joke interval in minutes

# WoW OST Path - Com verificação de existência
WOW_OST_FOLDER = "F:\\vordrassil\\music\\wow-ost"
WOW_ENABLED = os.path.exists(WOW_OST_FOLDER)

# Pastas de expansões do WoW
WOW_EXPANSION_DIRS = {
    "classic": ["1.0 Classic"],
    "tbc": ["2.0 The Burning Crusade"],
    "wotlk": ["3.0 Wrath of the Lich King"],
    "cata": ["4.0 Cataclysm"],
    "mop": ["5.0 Mists of Pandaria"],
    "wod": ["6.0 Warlords of Draenor"],
    "legion": ["7.0 Legion", "7.1 Return to Karazhan", "7.2 Tomb of Sargeras", "7.3 Shadows of Argus"],
    "bfa": ["8.0 Battle for Azeroth", "8.1 Tides of Vegeance", "8.2 Rise of Azshara", "8.3 Visions of N'Zoth"],
    "sl": ["9.0 Shadowlands", "9.1 Chains of Domination", "9.2 Eternity's End"],
    "df": ["10.0 Dragonflight", "10.1 Embers of Neltharion", "10.2 Guardians of the Dream"],
    "tww": ["11.0 The War Within", "11.0.7 Siren Isle"],
    "undermine": ["11.1 Undermine"]
}

# Verifica se a pasta WoW existe e cria configurações alternativas para debug
if not os.path.exists(WOW_OST_FOLDER):
    # Pasta alternativa para testes - verifica se existe uma pasta dentro do diretório do bot
    alt_wow_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wow-music")
    
    # Se existir uma pasta wow-music, use-a como alternativa
    if os.path.exists(alt_wow_folder):
        WOW_OST_FOLDER = alt_wow_folder
        WOW_ENABLED = True
        logging.info(f"Usando pasta alternativa para músicas do WoW: {alt_wow_folder}")
        
        # Simplifica as pastas para testes
        WOW_EXPANSION_DIRS = {
            "classic": ["classic"],
            "tbc": ["tbc"],
            "wotlk": ["wotlk"],
            "cata": ["cata"],
            "mop": ["mop"],
            "wod": ["wod"],
            "legion": ["legion"],
            "bfa": ["bfa"],
            "sl": ["shadowlands"],
            "df": ["dragonflight"],
            "tww": ["tww"],
            "undermine": ["undermine"]
        }
    else:
        # Se a pasta não existir, definimos como vazio para evitar erros
        WOW_EXPANSION_DIRS = {}

# Version (adicionado de volta para evitar erros em misc_commands.py)
VERSION = "1.0.1"

# Create necessary directories
os.makedirs(AUDIO_FOLDER, exist_ok=True)
