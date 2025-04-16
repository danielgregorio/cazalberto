import os
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

# Create necessary directories
os.makedirs(AUDIO_FOLDER, exist_ok=True)
