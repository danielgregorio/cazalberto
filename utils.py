import json
import os
import logging
import aiohttp
import aiofiles
from typing import Dict, Any, Union, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def load_json(file: str) -> Dict[str, Any]:
    """Load JSON data from a file with error handling."""
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"⚠️ Erro: Arquivo {file} corrompido, resetando arquivo.")
            return {}
    return {}

def save_json(file: str, data: Dict[str, Any]) -> None:
    """Save JSON data to a file."""
    # Garante que o diretório existe
    os.makedirs(os.path.dirname(file), exist_ok=True)
    
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def ensure_folder(folder: str) -> None:
    """Ensure a directory exists."""
    if not os.path.exists(folder):
        os.makedirs(folder)

async def download_file(url: str, filepath: str) -> bool:
    """Download a file from a URL to the given filepath."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(await response.read())
                    logging.info(f"✅ Arquivo baixado com sucesso: {filepath}")
                    return True
                else:
                    logging.error(f"❌ Erro ao baixar arquivo: Status {response.status}")
    except Exception as e:
        logging.error(f"❌ Erro ao baixar arquivo: {e}")
    return False

def sanitize_name(name: str) -> str:
    """Sanitize a name for filesystem use, removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def truncate_text(text: str, max_length: int = 1900) -> Union[str, list]:
    """
    Truncate text to fit within Discord's message limit.
    Returns either a single string or a list of chunks.
    """
    if len(text) <= max_length:
        return text
    
    # Split into multiple chunks
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:  # +1 for newline
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
