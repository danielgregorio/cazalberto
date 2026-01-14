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
FAVORITES_FILE = "favorites.json"
STATS_FILE = "stats.json"

# Joke System
JOKES_FILE = "jokes.json"
ICEBREAKER_FILE = "icebreaker.json"
DEFAULT_JOKE_INTERVAL = 15  # Default joke interval in minutes

# Rate Limiting
RATE_LIMIT_COMMANDS = int(os.getenv("RATE_LIMIT_COMMANDS", "5"))  # Max commands
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "10"))  # Per X seconds

# WoW OST Configuration - Configurável via .env
# Prioridade: 1) WOW_OST_FOLDER do .env, 2) pasta wow-music local, 3) desabilitado
def get_wow_config():
    """
    Detecta e configura o caminho das músicas do WoW.
    Retorna tupla (wow_folder, wow_enabled, expansion_dirs)
    """
    # Tenta obter do .env primeiro
    env_wow_folder = os.getenv("WOW_OST_FOLDER")

    # Caminho alternativo local (relativo ao projeto)
    local_wow_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wow-music")

    # Diretórios de expansões completos (estrutura original)
    full_expansion_dirs = {
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

    # Diretórios simplificados para estrutura local
    simple_expansion_dirs = {
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

    # Verifica qual configuração usar
    if env_wow_folder and os.path.exists(env_wow_folder):
        # Usa pasta do .env
        logging.info(f"WoW OST: Usando pasta configurada via .env: {env_wow_folder}")
        # Detecta se é estrutura completa ou simplificada
        # Verifica se existe uma subpasta com nome de expansão completa
        test_dir = os.path.join(env_wow_folder, "1.0 Classic")
        if os.path.exists(test_dir):
            return env_wow_folder, True, full_expansion_dirs
        else:
            return env_wow_folder, True, simple_expansion_dirs

    elif os.path.exists(local_wow_folder):
        # Usa pasta local wow-music
        logging.info(f"WoW OST: Usando pasta local: {local_wow_folder}")
        return local_wow_folder, True, simple_expansion_dirs

    else:
        # WoW desabilitado
        logging.warning("WoW OST: Nenhuma pasta de músicas encontrada. Modo WoW desabilitado.")
        logging.info("  -> Configure WOW_OST_FOLDER no .env ou crie uma pasta 'wow-music' no diretório do bot.")
        return None, False, {}

# Aplica configuração do WoW
WOW_OST_FOLDER, WOW_ENABLED, WOW_EXPANSION_DIRS = get_wow_config()

# Version
VERSION = "2.0.0"

# Create necessary directories
os.makedirs(AUDIO_FOLDER, exist_ok=True)
